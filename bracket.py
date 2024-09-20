import json
import itertools
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
    # TODO: revisit seeding strategy
    # maybe don't worry about number of groups, let bracket lib take care of byes
    # see algo description at https://en.wikipedia.org/wiki/Serpentine_system
    def __init__(self, groups, num_advance=2):
        self.groups = groups
        self.num_advance = num_advance
        self.more_advance_group_size = None
        self.fewer_advance_group_size = None

    @staticmethod
    def _seed_groups(players, preferred_group_size):
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

        return groups

    @staticmethod
    def _snake_seed_groups(players, preferred_group_size, group_rounding_strat='up'):
        # fill groups with "snake" style seeding
        # this should reverse the groups after every pass
        # is the only difference
        #
        players.sort(key=lambda p: -1 * p.rating)
        # determine group rounding strategy
        # e.g. would we rather allow some groups to have 1 less or some groups to have 1 more than preferred
        q, r = divmod(len(players), preferred_group_size)
        num_groups = 0
        if group_rounding_strat == 'up':
            num_groups = q
        elif group_rounding_strat == 'down':
            num_groups = q
            if r > 0:
                print('adding one to number of groups for rounding strategy "down"')
                num_groups += 1
        else:
            raise ValueError('group_rounding_strat must be one of ("up", "down")')

        groups = [] 
        for _ in range(num_groups):
            groups.append([])
        # populate the groups with players
        group = []
        num_players = len(players)
        for i in range(num_players):
            # append sorted players to different groups 
            # want to avoid putting the two highest rated players 
            # in the same group for example
            group_idx = i % num_groups
            # for each pass, reverse the groups that we have
            # this is "snake" seeding
            # when group_idx is 0 we have finished the pass through the list of groups
            if group_idx == 0:
                groups.reverse()
            p = players.pop(0)
            groups[group_idx].append(p)

        return groups

    @classmethod
    def from_players_list(cls, players, preferred_group_size=4, group_rounding_strat='up'):
        # populate player groups and make seeded bracket
        groups = cls._snake_seed_groups(
            players=players,
            preferred_group_size=preferred_group_size,
            group_rounding_strat=group_rounding_strat
        )

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

    def print_groups(self, display_rating=False):
        letters = ['A', 'B', 'C', 'D', 'E']

        print(f'TOTAL GROUPS: {len(self.groups)}')
        print()
        for group in self.groups:
            num_advance = self.num_advance
            # check for exceptions
            if self.more_advance_group_size == len(group.players):
                num_advance += 1
            elif self.fewer_advance_group_size == len(group.players):
                num_advance -= 1
            print(f'GROUP {group.group_number} - top {num_advance} advance')
            print('-' * 40)
            for i, player in enumerate(group.players):
                player_str = f'{letters[i]}) {player.name}' 
                if display_rating:
                    player_str = f'{player_str} ({player.rating})'
                print(player_str)
            # print match order
            player_letters = letters[0: len(group.players)]
            matches = make_rr_matches(player_letters)
            print()
            for i, (p1, p2) in enumerate(matches):
                print(f'  {i + 1}. {p1} vs {p2}')
            print()

    def display(self):
        team_labels = []
        place_suffixes = {
            1: 'st',
            2: 'nd',
            3: 'rd'
        }
        # accounting for when we set num_advance exceptions for group size.
        fewer_advance_size = None
        # if we have "more players advance" for a particular group size, the
        # max possible that can advance is num_advance + 1
        max_players_advance = self.num_advance
        if self.more_advance_group_size is not None:
            max_players_advance += 1
            fewer_advance_size = self.more_advance_group_size - 1
        # check if we have set fewer advance group size
        if self.fewer_advance_group_size is not None:
            fewer_advance_size = self.fewer_advance_group_size
        # determine group size for which fewer should advance
        for n in range(max_players_advance):
            for group in self.groups:
                # check if we have exceptions for this group size
                if fewer_advance_size is not None and len(group.players) == fewer_advance_size:
                    if self.more_advance_group_size is not None and n + 1 > self.num_advance:
                        continue
                    elif self.fewer_advance_group_size is not None and n + 1 > self.num_advance - 1:
                        continue

                # 1st 2nd 3rd suffixes e.g. "nd"
                place = n + 1
                # default to "th" if there's not an exception for it
                place_suffix = place_suffixes.get(place, 'th')
                label = f'Group {group.group_number} {place}{place_suffix} place'
                team_labels.append(label)
        # instantiate bracket class
        bviz = BracketViz(team_labels)
        #bviz.shuffle()
        bviz.show()


def make_rr_matches(letters):
    pairs = list(itertools.combinations(letters, 2))
    matches = []
    for i in range(len(pairs)):
        if i % 2 == 0:
            pair = pairs.pop(0)
        else:
            pair = pairs.pop(-1)
        matches.append(pair)
    matches.reverse()
    return matches

def load_players_file(players_file):
    players = []
    with open(players_file) as f:
        reader = csv.reader(f)
        for row in reader:
            if row[2].strip() == 'Y':
                players.append(Player(row[0], int(row[1])))

    return players


if __name__ == '__main__':
    import csv
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', "--group_size", default=4, type=int, help="preferred group size to use for RR groups") 
    parser.add_argument('-r', "--group_rounding", default='up', help="allowed values ('up', 'down'). A value of 'up' allows for groups greater than preferred group size, 'down' allows for smaller")
    parser.add_argument('-i', "--input_file", default='input/players.csv', help="input csv file of player 'name', 'rating'")
    parser.add_argument('-n', "--num_advance", default=2, type=int, help="number of players that advance to the main draw from each RR group")
    parser.add_argument('-f', "--fewer_advance_for_grp_size", type=int, help="if group size == <this param> 1 fewer player advances")
    parser.add_argument('-m', "--more_advance_for_grp_size", type=int, help="if group size == <this param> 1 more player advances")
    parser.add_argument('-d', "--display_rating", action='store_true', help="number of players that advance to the main draw from each RR group")

    args = parser.parse_args()

    players = load_players_file(args.input_file)

    bracket = Bracket.from_players_list(
        players, 
        preferred_group_size=args.group_size,
        group_rounding_strat=args.group_rounding
    )
    bracket.num_advance = args.num_advance
    # set any exceptions for group size and num_advance
    if args.fewer_advance_for_grp_size:
        bracket.fewer_advance_group_size = args.fewer_advance_for_grp_size
    if args.more_advance_for_grp_size:
        bracket.more_advance_group_size = args.more_advance_for_grp_size
    bracket.print_groups(display_rating=args.display_rating)
    print()
    bracket.display()
    print()
