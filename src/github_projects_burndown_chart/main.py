import argparse

from chart.burndown import *
from config import config
from discord import webhook
from gh.api_wrapper import get_organization_project, get_repository_project, get_project_v2
from gh.project import Project
from util import calculators, colors
from util.stats import *
from util.calculators import *

from pprint import pprint

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description='Generate a burndown chart for a GitHub project.')
    parser.add_argument("--filepath",
                        help="The filepath where the burndown chart is saved.")
    parser.add_argument("--discord", action='store_true',
                        help="If present, posts the burndown chart to the configured webhook")
    return parser.parse_args()


def download_project_data(project_type: str, project_version: int) -> Project:
    if project_version == 2:
        return get_project_v2(project_type)

    if project_type == 'repository':
        return get_repository_project()
    elif project_type == 'organization':
        return get_organization_project()


def prepare_chart_data(stats: ProjectStats, sprint_name):
    color = colors()
    data = BurndownChartData(
        sprint_name=sprint_name,
        utc_chart_start=config.utc_sprint_start(),
        utc_chart_end=config.utc_chart_end() or config.utc_sprint_end(),
        utc_sprint_start=config.utc_sprint_start(),
        utc_sprint_end=config.utc_sprint_end(),
        total_points=stats.total_points,
        series=[
            BurndownChartDataSeries(
                name=pts_type,
                data=stats.remaining_points_by_date(
                    calculators(stats.project)[pts_type]),
                format=dict(color=next(color))
            ) for pts_type in config['settings'].get('calculators', ['closed'])
        ],
        points_label=f"Outstanding {'Points' if config['settings']['points_label'] else 'Issues'}"
    )
    return data


if __name__ == '__main__':
    args = parse_cli_args()
    config.set_project("organization", "TF-Real-Time-Digital-Replica-of-Traffic-Flow")
    project = download_project_data("organization", config['settings'].get('version', 1))
    stats = ProjectStats(project, config.utc_sprint_start(),
                         config.utc_chart_end() or config.utc_sprint_end())
    # Generate the burndown chart
    pprint(stats)
    burndown_chart = BurndownChart(prepare_chart_data(stats, config['settings'].get("sprint")), stats.project.total_points)
    if args.discord:
        chart_path = "./tmp/chart.png"
        burndown_chart.generate_chart(chart_path)
        webhook.post_burndown_chart(chart_path)
    elif args.filepath:
        burndown_chart.generate_chart(args.filepath)
    else:
        burndown_chart.render()
    print('Done')
