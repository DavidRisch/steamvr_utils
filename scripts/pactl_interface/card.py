#!/usr/bin/python3

import re

import log

from . import utlis


class Card:
    class Profile:
        def __init__(self, line):
            self.name = None
            self.human_name = None

            match = re.match(r'^([^ ]*): (.*) \(.*\)$', line)
            if match is not None:
                self.name = match.group(1)
                self.human_name = match.group(2)

        def __repr__(self):
            return '<PROFILE name: {}, human_name: {}>'.format(self.name, self.human_name)

    class Port:
        def __init__(self, in_dict, card):
            self.product_name = None
            self.profiles = []
            self.card = card

            key, contents = list(in_dict.items())[0]

            match = re.match('^(.*): ', key)
            self.name = match.group(1)

            for content in contents:
                if 'Properties:' in content:
                    for property_item in content['Properties:']:
                        if isinstance(property_item, dict):
                            property_item, _ = list(property_item.items())[0]
                        match = re.match('^device.product.name = \"(.*)$', property_item)
                        if match is not None:
                            self.product_name = match.group(1)
                else:
                    match = re.match(r'^Part of profile\(s\): (.*)$', content)
                    if match is not None:
                        profile_names = match.group(1).split(', ')
                        for profile_name in profile_names:
                            matching_profiles = [
                                profile for profile in card.profiles
                                if profile.name == profile_name
                            ]
                            if len(matching_profiles) == 1:
                                self.profiles.append(matching_profiles[0])
                            else:
                                log.w('Did not find profile {}'.format(profile_name))

        def __eq__(self, other):
            if isinstance(other, type(self)):
                return self.card == self.card and self.name == other.name
            return False

        def __repr__(self):
            return '<PORT name: {}, product_name: {}, profiles: {}>'.format(
                self.name, self.product_name, self.profiles)

    def __init__(self, in_dict):
        self.name = None
        self.profiles = None
        self.ports = None

        card_dict = list(in_dict.items())[0][1]

        for item in card_dict:
            if isinstance(item, str):
                match = re.match('^Name: (.*)$', item)
                if match is not None:
                    self.name = match.group(1)

            elif isinstance(item, dict):
                key, content = list(item.items())[0]
                if key == 'Profiles:':
                    self.profiles = []
                    for profile_dict in content:
                        self.profiles.append(self.Profile(profile_dict))
                if key == 'Ports:':
                    self.ports = []
                    for port_dict in content:
                        self.ports.append(self.Port(port_dict, self))

        if self.name is None or self.ports is None:
            raise RuntimeError('Parsing of card failed:\n{}'.format(in_dict))

    def set_profile(self, config, profile):
        if config.dry_run():
            log.w('Skipping because of dry run')
            return

        arguments = ['pactl', 'set-card-profile', self.name, profile.name]
        return_code, stdout, stderr = utlis.run(arguments)

        if return_code != 0:
            log.e('\'{}\' () failed, stderr:\n{}'.format(" ".join(arguments), stderr))

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.name == other.name
        return False

    def __repr__(self):
        return '<CARD name: {}, profiles: {}, ports: {}>'.format(self.name, self.profiles, self.ports)

    @staticmethod
    def rescan_all_cards():
        arguments = ['pactl', 'load-module', 'module-detect']
        return_code, stdout, stderr = utlis.run(arguments)

        if return_code != 0:
            log.e('\'{}\' () failed, stderr:\n{}'.format(" ".join(arguments), stderr))

    @classmethod
    def get_all_cards(cls):
        arguments = ['pactl', 'list', 'cards']
        return_code, stdout, stderr = utlis.run(arguments)

        cards = stdout

        class Node:
            # https://stackoverflow.com/a/53346240/13623303
            def __init__(self, indented_line):
                self.children = []
                self.level = len(indented_line) - len(indented_line.lstrip())
                self.text = indented_line.strip()

            def add_children(self, nodes):
                child_level = nodes[0].level
                while nodes:
                    node = nodes.pop(0)
                    if node.level == child_level:  # add node as a child
                        self.children.append(node)
                    elif node.level > child_level:  # add nodes as grandchildren of the last child
                        nodes.insert(0, node)
                        self.children[-1].add_children(nodes)
                    elif node.level <= self.level:  # this node is a sibling, no more children
                        nodes.insert(0, node)
                        return

            def as_dict(self):
                if len(self.children) > 0:
                    return {self.text: [node.as_dict() for node in self.children]}
                else:
                    return self.text

        root = Node('root')
        root.add_children([Node(line) for line in cards.splitlines() if line.strip()])

        cards = []

        for card_dict in root.as_dict()['root']:
            cards.append(cls(card_dict))

        return cards


if __name__ == '__main__':
    print(Card.get_all_cards())
