import anvil

# Each file represents different arena bounds
# Use x (left right) and z (forward back) 
region_files = [
    ("Aquarium/region/r.0.0.mca", 0, 0), # Origin
    ("Aquarium/region/r.-1.0.mca", -1, 0), # West of origin
    ("Aquarium/region/r.0.-1.mca", 0, -1), # South of origin
    ("Aquarium/region/r.-1.-1.mca", -1, -1), # Southwest of origin
]

# Number based Categories
# Maps block id to category
# Everything not listed defaults to solid (1)
BLOCK_ID_TO_CATEGORY = {
    0:   0,  # air
    26:  2,  # bed — the objective to defend/destroy
    57:  4,  # diamond block — generator
    133: 4,  # emerald block — generator
    121: 7,  # end stone — placeable defense block
    35:  6,  # wool (all colors) — team base markers / placeable defense
}

# Find bounding boxes
min_x = min_y = min_z = float('inf')
max_x = max_y = max_z = float('-inf')

for filename, reg_x, reg_z in region_files:
    region = anvil.Region.from_file(filename)

    # Iterate over chunks and extract blocks
    # Each region has 32x32 chunks
    for chunk_x in range(32):
        for chunk_z in range(32):
            try:
                # Get raw chunk data object
                nbt_data = region.chunk_data(chunk_x, chunk_z)
                if nbt_data is None:
                    continue
                # Bypass Chunk.__init__ which requires DataVersion
                chunk = object.__new__(anvil.Chunk)
                chunk.version = 0  # pre-1.13
                chunk.data = nbt_data['Level']
                chunk.x = chunk.data['xPos'].value
                chunk.z = chunk.data['zPos'].value
                chunk.tile_entities = chunk.data['TileEntities']
            except Exception:
                continue
            if chunk is None:
                continue

            # Get the coordinate of this chunk in the world space
            world_cx = (reg_x * 32 + chunk_x) * 16
            world_cz = (reg_z * 32 + chunk_z) * 16

            # Scan each block in the chunk and exclude air blocks 
            # Each chunk is 16x256x16
            # Pre-1.13: block.id is numeric (0 = air)
            for y in range(256):
                for x in range(16):
                    for z in range(16):
                        block = chunk.get_block(x, y, z)
                        if block.id != 0:
                            # Location relative to its origin
                            wx = world_cx + x 
                            wz = world_cz + z
                            # Get the bounds
                            min_x = min(min_x, wx)
                            max_x = max(max_x, wx)
                            min_y = min(min_y, y)
                            max_y = max(max_y, y)
                            min_z = min(min_z, wz)
                            max_z = max(max_z, wz)

    print(f"Bounding box:")
    print(f"  X: {min_x} to {max_x}  (width: {max_x - min_x + 1})")
    print(f"  Y: {min_y} to {max_y}  (height: {max_y - min_y + 1})")
    print(f"  Z: {min_z} to {max_z}  (depth: {max_z - min_z + 1})")

# Build 3D voxel array to represent minecraft blocks
W = max_x - min_x + 1 # Full width of world
H = max_y - min_y + 1 # Height
D = max_z - min_z + 1 # Depth

# Default to air (zeros)
voxels = np.zeros((W, H, D), dtype = np.uint8)

# Map blocks at location to a new voxel
# voxels are set to the block's category
for wx, y, wz, block_id in blocks:
    voxels[wx - min_x, y - min_y, wz - min_z] = BLOCK_ID_TO_CATEGORY.get(block_id, 1)  # default: solid

# Mark void objects
# All objects under the lowest solid block
for xi in range(W):
    for zi in range(D):
        for yi in range(H):
            if voxels[xi, yi, zi] != 0:  # not air
                break
            voxels[xi, yi, zi] = 5  # void