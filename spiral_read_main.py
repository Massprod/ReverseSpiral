from aiohttp import ClientSession, ClientTimeout, ClientConnectorError
from aiohttp.client_exceptions import InvalidURL


async def spiral_read(matrix: list[list[int]]) -> list[int]:
    """
    Reads the matrix in counter-clockwise spiral order.
    Starting from NW corner == matrix[0][0]

    :param matrix: of any size.
    :return: all matrix values in counter-clockwise spiral order.
    """
    if len(matrix) == 0:
        return []
    max_x: int = len(matrix[0]) - 1
    spiral: list[int] = []
    # Only one column.
    if max_x == 0:
        for _ in matrix:
            spiral.append(_[0])
        return spiral
    max_y = len(matrix) - 1
    # Only one row.
    if max_y == 0:
        # We need counter-clock, row should be reversed.
        for x in range(len(matrix[0]) - 1, -1, -1):
            spiral.append(matrix[0][x])
        return spiral
    all_steps: int = len(matrix[0]) * len(matrix)
    x: int = 0
    dx: int = 0
    y: int = 0
    dy: int = 1
    steps: int = 1
    turn: int = 0
    min_x: int = 0
    min_y: int = 0
    spiral = [matrix[y][x]]
    while steps < all_steps:
        if turn % 3 == 0 and turn == 3:
            min_x += 1
            max_x -= 1
            turn += 1
        elif turn % 5 == 0 and turn == 5:
            min_y += 1
            max_y -= 1
            turn = 0
        x += dx
        y += dy
        spiral.append(matrix[y][x])
        if x == max_x and dy == 0 and dx == 1:
            dy, dx = -1, 0
            turn += 1
        elif y == max_y and dx == 0 and dy == 1:
            dy, dx = 0, 1
            turn += 1
        elif x == min_x and dy == 0 and dx == -1:
            dy, dx = 1, 0
            turn += 1
        elif y == min_y and dx == 0 and dy == -1:
            dy, dx = 0, -1
            turn += 1
        steps += 1
    return spiral


async def get_matrix(url: str) -> list[int] | str:
    """
    Makes GET request for input_URL.
    Takes all possible digits from response payload, separated by non-digits.
    Creates matrix from these values and if it's Square matrix reads in counter-clockwise spiral order.
    Otherwise, returns Error string.

    :param url: any URL string to work with.
    :return: correct counter-clockwise reading of given Matrix.
    """
    # Default 5m, but it's too much in our case.
    async with ClientSession(timeout=ClientTimeout(total=45)) as connect:
        try:
            async with connect.get(url) as response:
                # No reasons to handle all, and we can't do anything about server Errors anyway.
                # > 400, close connection inform.
                if not response.ok:
                    await connect.close()
                    if response.status == 400:
                        return f"Bad request {response.status}:\n{url}"
                    elif response.status == 401:
                        return f"Don't try to access services with authorization {response.status}:\n{url}"
                    elif response.status == 403:
                        return f'Forbidden access: {response.status}:\n{url}'
                    elif response.status == 404:
                        return f"Page doesn't exist {response.status}:\n{url}"
                    # Prefer to leave whole response, for everything uncovered.
                    return f'Something went wrong:\n{response}'
                orig_matrix: str = await response.text()
                await connect.close()
                all_values: list[int] = []
                cur_value: str = ''
                for sym in orig_matrix:
                    if sym.isdigit():
                        cur_value += sym
                    elif cur_value:
                        all_values.append(int(cur_value))
                        cur_value = ''
                # Empty page. Or no digits at all.
                if not all_values:
                    return f"No data to process from provided URL.\n{url}"
                # Case: len == 35, sqr(35) -> 5.9 int(5.9) => 5.
                # 35 % 5 == 0. So we need to check with float first.
                row_length: int | float = len(all_values) ** 0.5
                # Not square.
                if len(all_values) % row_length != 0:
                    return f"Provided matrix from {url} have incorrect type.\n" \
                            "Only square matrix's allowed.\n"
                # It's faster to cast float -> int then calc (** 0.5) again.
                row_length = int(row_length)
                correct_matrix: list[list[int]] = []
                for y in range(0, len(all_values), row_length):
                    correct_matrix.append([])
                    for x in range(y, y + row_length):
                        correct_matrix[-1].append(all_values[x])
                return await spiral_read(correct_matrix)

        except ClientConnectorError as error:
            return f'Connection error:\n{error}'
        except InvalidURL as error:
            return f'Incorrect URL:\n{error}'
        except TimeoutError:
            return f'Timeout, service is unreachable:\n{url}'
