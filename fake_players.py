
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


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', "--group_size", default=4, type=int)  
    parser.add_argument('-n', "--num_players", type=int)  
    args = parser.parse_args()

    players = make_fake_players(2050, args.num_players)
    bracket = Bracket.from_players_list(players, preferred_group_size=args.group_size, snake_seed=True)

    bracket.print_groups()
    print()
    bracket.display()
    print()
