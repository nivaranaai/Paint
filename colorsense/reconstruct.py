import pycolmap
import open3d as o3d
import os


def reconstruct_3d(image_dir, work_dir="media/reconstruction_output"):
    os.makedirs(work_dir, exist_ok=True)

    db_path = os.path.join(work_dir, "database.db")
    sparse_path = os.path.join(work_dir, "sparse")
   # dense_path = os.path.join(work_dir, "dense")
    os.makedirs(sparse_path, exist_ok=True)
    #os.makedirs(dense_path, exist_ok=True)

    # Step 1: Feature extraction
    pycolmap.extract_features(db_path, image_dir)

    # Step 2: Feature matching
    pycolmap.match_exhaustive(db_path)

    # Step 3: Sparse reconstruction
    pycolmap.incremental_mapping(db_path, image_dir, sparse_path)

    # Step 4: Dense reconstruction
    #pycolmap.stereo(image_dir, os.path.join(sparse_path, "0"), dense_path)

    ply_path = os.path.join(sparse_path, "fused.ply")
    return ply_path


def pointcloud_to_textured_mesh(ply_path, output_mesh="media/textured_mesh.obj"):
    # Load point cloud
    pcd = o3d.io.read_point_cloud(ply_path)

    if not pcd.has_normals():
        print("⚠️ No normals found — estimating...")
        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(
            radius=0.1, max_nn=30
        ))

    # If still too few points, fallback to Alpha Shape
    if len(pcd.points) < 500:  # Sparse recon may give very few points
        print("⚠️ Sparse point cloud is too small, using Alpha Shape mesh.")
        mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha=0.03)
    else:
        # Poisson reconstruction
        mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=8)

        # Crop to bounding box
        bbox = pcd.get_axis_aligned_bounding_box()
        mesh = mesh.crop(bbox)

    # Simplify mesh
    mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=20000)

    # Add vertex colors if available
    if pcd.has_colors():
        mesh.vertex_colors = pcd.colors

    # Save mesh
    o3d.io.write_triangle_mesh(output_mesh, mesh)
    return output_mesh

