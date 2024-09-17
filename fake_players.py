
from bracket import Player, Bracket

def make_fake_players(top_rating, num_players):
    players = []
    rating = top_rating
    for i in range(num_players):
        num = i + 1
        player_name = f'player_{i+1}'
        rating = rating - (3 * i)
        players.append(Player(player_name, rating))

    return players

def print_groups(bracket):
    letters = ['A', 'B', 'C', 'D', 'E']

    print(f'TOTAL GROUPS: {len(bracket.groups)}')
    print()
    for group in bracket.groups:
        print(f'GROUP {group.group_number}')
        print('-' * 40)
        for i, player in enumerate(group.players):
            print(f'{letters[i]}) {player.name} ({player.rating})')
        print()


if __name__ == '__main__':
    players = make_fake_players(2050, 15)
    bracket = Bracket.from_players_list(players, preferred_group_size=4)

    bracket.print_groups()
