import base64
import os
import re
from typing import List, Dict, Any

# Optional LangGraph integration (minimal)
try:
    from langgraph.graph import StateGraph, START, END  # type: ignore
    from typing import TypedDict
except Exception:  # pragma: no cover
    StateGraph = None  # type: ignore
    START = END = None  # type: ignore
    TypedDict = dict  # type: ignore


# OpenAI client wrapper (supports new and legacy SDKs)
class OpenAIClient:
    def __init__(self):
        self._client = None
        self._mode = None
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            try:
                from django.conf import settings as dj_settings  # type: ignore
                api_key = getattr(dj_settings, "OPENAI_API_KEY", None)
            except Exception:
                api_key = None
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment or Django settings.")
        try:
            # New SDK style
            from openai import OpenAI  # type: ignore
            self._client = OpenAI(api_key=api_key)
            self._mode = "new"
        except Exception:
            # Legacy SDK fallback
            import openai  # type: ignore
            openai.api_key = api_key
            self._client = openai
            self._mode = "legacy"

    def chat(self, model: str, messages: List[Dict[str, Any]]) -> str:
        if self._mode == "new":
            resp = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.6,
            )
        else:
            try:
                # Legacy SDK (<=0.x)
                resp = self._client.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=0.6,
                )
            except Exception:
                # Some environments expose the new-style endpoint on the module
                resp = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.6,
                )
        # Normalize return across SDKs
        try:
            return resp.choices[0].message.content or ""
        except Exception:
            return resp["choices"][0]["message"]["content"]


def file_to_data_url(upload) -> str:
    """Convert Django UploadedFile (image) to data URL for OpenAI vision input."""
    content_type = getattr(upload, "content_type", "application/octet-stream")
    data = upload.read()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:{content_type};base64,{b64}"


def build_messages(user_text: str, image_data_urls: List[str], doc_texts: List[str]) -> List[Dict[str, Any]]:
    
    system_prompt1 = (
        "You are PaintSense, a smart paint consultant.\n"
        "Given a user's room description, style preferences, and optional images of the space,\n"
        "recommend 3-5 paint color options (with HEX), finishes (eggshell/matte/semi-gloss), and brief rationales.\n"
        "If images are provided, infer lighting, existing furniture colors, and undertones.\n"
        "Be concise and practical. Close with preparation tips.\n"
        "Return approachable text; include HEX codes when naming colors." )

    system_prompt = (
        "Elaborate the text provided \n"
        "If images are provided, infer lighting, existing furniture colors, and undertones. also walls ceiling windows etc\n"
        "Be concise and practical. Close with preparation tips.\n"
        "Return approachable text."
    )

    content_parts: List[Dict[str, Any]] = []
    # Add user text
    if user_text:
        content_parts.append({"type": "text", "text": user_text})

    # Add doc texts if any
    if doc_texts:
        joined = "\n\n".join(doc_texts)[:6000]  # keep prompt size reasonable
        content_parts.append({"type": "text", "text": f"Additional notes from documents:\n{joined}"})

    # Add images as descriptions instead of URLs
    if image_data_urls:
        image_descriptions = "\n".join([f"Image {i+1}: [image description]" for i, _ in enumerate(image_data_urls)])
        content_parts.append({"type": "text", "text": f"Images provided:\n{image_descriptions}"})

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content_parts or user_text or "Suggest paint colors."},
    ]


def extract_hex_codes(text: str) -> List[str]:
    return list(dict.fromkeys(re.findall(r"#[0-9a-fA-F]{6}", text)))[:8]


class AgentState(TypedDict):  # type: ignore
    user_text: str
    image_data_urls: List[str]
    doc_texts: List[str]
    reply: str


def run_agent(user_text: str, image_uploads: List[Any], doc_uploads: List[Any]) -> Dict[str, Any]:
    """
    Orchestrate the process: summarize inputs, confirm summary, and generate paint suggestions.
    Returns dict with 'reply' and 'swatches' (list of hex codes).
    """
    client = OpenAIClient()

    # Convert images to data URLs
    image_data_urls: List[str] = []
    for img in image_uploads:
        try:
            if getattr(img, "content_type", "").startswith("image/"):
                image_data_urls.append(file_to_data_url(img))
        finally:
            img.seek(0)

    # Read document texts
    doc_texts: List[str] = []
    for doc in doc_uploads:
        try:
            name = getattr(doc, "name", "doc")
            if name.lower().endswith((".txt", ".md")):
                raw = doc.read().decode("utf-8", errors="ignore")
                doc_texts.append(raw[:8000])
            else:
                # Unsupported types for now
                pass
        finally:
            doc.seek(0)

    # Summarize inputs using LLM
    summary_messages = build_messages(user_text=user_text, image_data_urls=image_data_urls, doc_texts=doc_texts)
    summary_model = os.environ.get("SUMMARY_MODEL", "gpt-3.5-turbo")
    summary = client.chat(model=summary_model, messages=summary_messages)

    # Send summary to frontend for confirmation
    confirmation_response = {"reply": summary, "swatches": []}

    # Simulate confirmation response for testing
    # In a real scenario, this would be replaced by actual frontend response
    confirmation_response["confirm"] = True  # Simulate approval

    if confirmation_response.get("confirm", False):
        # Generate paint suggestions
        suggestion_messages = build_messages(user_text=summary, image_data_urls=image_data_urls, doc_texts=doc_texts)
        suggestion_model = os.environ.get("PAINTSENSE_MODEL", "gpt-4o-mini")
        suggestion_reply = client.chat(model=suggestion_model, messages=suggestion_messages)
        swatches = extract_hex_codes(suggestion_reply)

        return {
            "reply": suggestion_reply,
            "swatches": swatches,
        }
    else:
        return {"reply": "Summary rejected. Please revise the input.", "swatches": []}


def _review_node(state: AgentState) -> AgentState:
    """Human-in-the-loop review node for confirming the summary via frontend."""
    # This node should be handled by the frontend confirmation process
    # The state will be updated based on the frontend response
    # For now, simulate approval for testing purposes
    state["reply"] = "Summary approved. Proceeding with paint suggestions."
    return state

# Optional: LangGraph wrapper (single node) - not strictly necessary but available
if StateGraph is not None:
    def _call_node(state: AgentState) -> AgentState:  # type: ignore
        result = run_agent(
            user_text=state.get("user_text", ""),
            image_uploads=[],  # handled in run_agent normally; this wrapper expects only text/docs
            doc_uploads=[],
        )
        state["reply"] = result["reply"]
        return state

    graph = StateGraph(AgentState)  # type: ignore
    graph.add_node("call_openai", _call_node)  # type: ignore
    graph.add_node("review", _review_node)
    graph.add_edge(START, "call_openai")  # type: ignore
    graph.add_edge("call_openai", "review")  # type: ignore
    graph.add_edge("review", END)  # type: ignore
    PAINT_GRAPH = graph.compile()  # type: ignore
else:
    PAINT_GRAPH = None
