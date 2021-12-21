# language=markdown
"""
This module provides the definition of class `Method` that contains definitions of interpolation methods used.

Objects of this class are used to:

* generate SQL tables, and functions related to data interpolation;
* insert data in SQL tables that contain interpolated data.

The variable `METHODS` contains a list of interpolation methods that are used in the EXPOLIS project.
"""

from typing import Callable, List

from resolution import Resolution


class Method:
    """
    Represents common characteristics of interpolation methods.
    """
    def __init__ (
            self,
            sql_identifier: str,
            description: str,
            command_line_arguments: Callable[..., List[str]],
    ):
        """
        Construct the characteristics of an interpolation method.
        :param sql_identifier: the sql identifier that is used in SQL tables and functions
        that deal with data interpolation.
        :param description human-readable description of the interpolation method.
        :param command_line_arguments command line arguments to run the interpolation algorithm
        """
        self.sql_identifier = sql_identifier
        self.description = description
        self.command_line_arguments = command_line_arguments


def __kriging_command_line_arguments__ (
        resolution: Resolution
) -> List[str]:
    return [
        '/opt/expolis/bin/interpolator-kriging',
        '--min-longitude', '-9.258299',
        '--max-longitude', '-8.895191',
        '--min-latitude', '38.397111',
        '--max-latitude', '38.703961',
        '--grid-cell-size', '{}'.format (min (resolution.cell_longitude_size, resolution.cell_latitude_size)),
    ]


KRIGING = Method (
    sql_identifier='kriging',
    description='kriging',
    command_line_arguments=__kriging_command_line_arguments__,
)

METHODS = [
    KRIGING,
]
