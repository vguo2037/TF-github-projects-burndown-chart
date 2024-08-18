from datetime import datetime
from dateutil.parser import isoparse

from config import config
from pprint import pprint

class Project:
    columns = None

    @property
    def total_points(self):
        return sum([column.get_total_points() for column in self.columns])

    @property
    def cards(self):
        return [card for column in self.columns for card in column.cards]


class ProjectV1(Project):
    def __init__(self, project_data):
        self.name = project_data['name']
        self.columns = self.__parse_columns(project_data)

    def __parse_columns(self, project_data):
        columns_data = project_data['columns']['nodes']
        columns = [Column(self.__parse_cards(column_data)) for column_data in columns_data]
        return columns

    def __parse_cards(self, column_data):
        cards_data = column_data['cards']['nodes']
        cards = [Card(card_data) for card_data in cards_data]
        return cards


class ProjectV2(Project):
    def __init__(self, project_data):
        self.name = project_data['title']
        self.columns = self.__parse_columns(project_data)

    def __parse_columns(self, project_data):
        column_dict = {None: []}
        for option in project_data['field']['options']:
            column_dict[option['name']] = []

        for item_data in project_data['items']['nodes']:
            status = (item_data.get('status') or {}).get('name')
            column_dict[status].append(Card(item_data))

        columns = [Column(column_key, column_dict[column_key]) for column_key in column_dict.keys()]

        pprint(column_dict)
        return columns


class Column:
    def __init__(self, key, cards):
        self.cards = cards

        if key == "Done":
            for c in self.cards:
                c.closed = c.closed if c.closed is not None else config.utc_sprint_end()

    def get_total_points(self):
        return sum([card.points for card in self.cards])


class Card:
    def __init__(self, card_data):
        self.points = self.__parse_points(card_data)
        self.sprint = self.__parse_sprint(card_data)

        card_data = card_data['content'] if card_data['content'] else card_data
        self.created: datetime = self.__parse_createdAt(card_data)
        self.assigned: datetime = self.__parse_assignedAt(card_data)
        self.closed: datetime = self.__parse_closedAt(card_data)

    def __parse_assignedAt(self, card_data) -> datetime:
        assignedAt = None
        assignedDates = card_data.get('timelineItems', {}).get('nodes', [])
        if assignedDates:
            assignedAt = isoparse(assignedDates[0]['createdAt'])
        return assignedAt

    def __parse_createdAt(self, card_data) -> datetime:
        createdAt = None
        if card_data.get('createdAt'):
            createdAt = isoparse(card_data['createdAt'])
        return createdAt

    def __parse_closedAt(self, card_data) -> datetime:
        closedAt = None
        if card_data.get('closedAt'):
            closedAt = isoparse(card_data['closedAt'])
        return closedAt

    def __parse_points(self, card_data) -> int:
        card_points = 0
        points_label = card_data.get('storyPoints')
        if not points_label:
            card_points = 0
        else:
            card_points = points_label.get('number')

        return card_points

    def __parse_sprint(self, card_data) -> int:

        sprint_label = card_data.get('sprint')
        if not sprint_label:
            card_sprint = None
        else:
            card_sprint = sprint_label.get('title')

        return card_sprint
