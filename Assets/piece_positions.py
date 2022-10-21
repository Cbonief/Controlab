from numpy import zeros

tile_positions = zeros((24, 2), dtype=int)

tile_positions[0] = [24, 24]
tile_positions[1] = [24, 300]
tile_positions[2] = [24, 600 - 24]

tile_positions[3] = [116, 116]
tile_positions[4] = [116, 300]
tile_positions[5] = [116, 600 - 116]

tile_positions[6] = [208, 208]
tile_positions[7] = [208, 300]
tile_positions[8] = [208, 600 - 208]

tile_positions[9] = [600 - 208, 208]
tile_positions[10] = [600 - 208, 300]
tile_positions[11] = [600 - 208, 600 - 208]

tile_positions[12] = [600 - 116, 116]
tile_positions[13] = [600 - 116, 300]
tile_positions[14] = [600 - 116, 600 - 116]

tile_positions[15] = [600 - 24, 24]
tile_positions[16] = [600 - 24, 300]
tile_positions[17] = [600 - 24, 600 - 24]

tile_positions[18] = [300, 24]
tile_positions[19] = [300, 116]
tile_positions[20] = [300, 208]

tile_positions[21] = [300, 600 - 208]
tile_positions[22] = [300, 600 - 116]
tile_positions[23] = [300, 600 - 24]


def adjacent_positions(pos):
    if pos == 0:
        return [1, 18]
    elif pos == 1:
        return [0, 2, 4]
    elif pos == 2:
        return [1, 23]
    elif pos == 3:
        return [19, 4]
    elif pos == 4:
        return [3, 1, 5, 7]
    elif pos == 5:
        return [4, 22]
    elif pos == 6:
        return [20, 7]
    elif pos == 7:
        return [6, 4, 8]
    elif pos == 8:
        return [7, 21]
    elif pos == 9:
        return [20, 10]
    elif pos == 10:
        return [9, 13, 11]
    elif pos == 11:
        return [10, 21]
    elif pos == 12:
        return [19, 13]
    elif pos == 13:
        return [12, 10, 14, 16]
    elif pos == 14:
        return [22, 13]
    elif pos == 15:
        return [18, 16]
    elif pos == 16:
        return [15, 13, 17]
    elif pos == 17:
        return [16, 23]
    elif pos == 18:
        return [0, 15, 19]
    elif pos == 19:
        return [18, 3, 12, 20]
    elif pos == 20:
        return [19, 6, 9]
    elif pos == 21:
        return [8, 11, 22]
    elif pos == 22:
        return [21, 5, 14, 23]
    elif pos == 23:
        return [22, 2, 17]
    else:
        return None


possible_mills = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [9, 10, 11],
    [12, 13, 14],
    [15, 16, 17],
    [18, 19, 20],
    [21, 22, 23],
    [0, 18, 15],
    [3, 19, 12],
    [6, 20, 9],
    [8, 21, 11],
    [5, 22, 14],
    [2, 23, 17],
    [1, 4, 7],
    [10, 13, 16],
]


adjacency_list = []
for tile_i in range(0, 24):
    adjacency_list.append(adjacent_positions(tile_i))


def is_position_adjacent(this_position, other_position):
    for adjacente in adjacency_list[this_position]:
        if adjacente == other_position:
            return True
    return False


# for i in range(0, 8):
#     print("-----------------")
#     for j in range(0, 8):
#         if adj_list[i][j]:
#             print("[{},{}] -> {}".format(i,j, adj_list[i][j]))

board = zeros(24, dtype=int)
