import json
from lib.bracket_viz import Bracket as BracketViz


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

        # sort players in each group
        groups = [sorted(g, key=lambda p: -1 * p.rating) for g in groups]
        groups = [Group(players=g, group_number=0) for g in groups]
        # sort groups by seed
        groups = sorted(groups, key=lambda g: -1 * g.get_max_rating())
        # update groups number to match seed
        for i, g in enumerate(groups):
            g.group_number = i + 1
        #
        return cls(groups=groups)

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

    def display(self):
        team_labels = []
        for group in self.groups:
            label = f'Group {group.group_number} 1st'
            team_labels.append(label)
        for group in self.groups:
            label = f'Group {group.group_number} 2nd'
            team_labels.append(label)
        # instantiate bracket class
        bviz = BracketViz(team_labels)
        #bviz.shuffle()
        bviz.show()



if __name__ == '__main__':
    import csv
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', "--group_size", default=4, type=int)    
    args = parser.parse_args()


    players = []
    with open('players.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            players.append(Player(row[0], int(row[1])))

    bracket = Bracket.from_players_list(players, preferred_group_size=args.group_size)
    bracket.print_groups()
    print()
    bracket.display()
    print()
