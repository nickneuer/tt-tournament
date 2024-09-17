import json


class Player():
    def __init__(self, name, rating):
        self.name = name
        self.rating = rating

    def __repr__(self):
        return f'Player({self.name}, {self.rating})'


class Group():
    def __init__(self, players, group_number):
        self.players = players
        self.group_number = group_number

    def get_max_rating(self):
        return sorted(self.players, key=lambda p: p.rating)[-1].rating

    def __repr__(self):
        return f'''Group(
    players={json.dumps([p.__repr__() for p in self.players], indent=4)}, 
    group_number={self.group_number}
)
'''


class Bracket():
    def __init__(self, groups):
        self.groups = groups
        self.num_advance = 2

    @classmethod
    def from_players_list(cls, players, preferred_group_size=4):
        # for simplicity just making this only work for 2 advance
        # make groups
        groups = []
        group = []
        for i in range(len(players)):
            # alternate group filling by pairing high seeded players
            # with lower seeded ones
            if i % 2 == 0:
                p = players.pop(0)
            else:
                p = players.pop(-1)
            group.append(p)
            if len(group) == preferred_group_size:
                groups.append(group)
                group = []
        # check for a remainder group of < preferred_group_size
        if group:
            groups.append(group)
        # handle group adjustment when there is a remainer group
        if len(groups) % 2 != 0:
            last_group = groups.pop(-1)
            groups.reverse()
            for i, player in enumerate(last_group):
                groups[i].append(player)

        groups = [sorted(g, key=lambda p: -1 * p.rating) for g in groups]
        final_groups = [Group(players=g, group_number=i+1) for i, g in enumerate(groups)]
        #
        return cls(groups=final_groups)

    def print_groups(self):
        letters = ['A', 'B', 'C', 'D', 'E']

        print(f'TOTAL GROUPS: {len(self.groups)}')
        print()
        for group in self.groups:
            print(f'GROUP {group.group_number}')
            print('-' * 40)
            for i, player in enumerate(group.players):
                print(f'{letters[i]}) {player.name} ({player.rating})')
            print()


if __name__ == '__main__':
    import csv 

    players = []
    with open('players.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            players.append(Player(row[0], int(row[1])))

    bracket = Bracket.from_players_list(players, preferred_group_size=3)
    bracket.print_groups()
