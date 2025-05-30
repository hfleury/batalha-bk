def coordinate_to_tuple(coord: str) -> tuple[int, int]:
    letter = coord[0]
    number = int(coord[1:])
    return (number - 1, ord(letter) - ord("A"))
