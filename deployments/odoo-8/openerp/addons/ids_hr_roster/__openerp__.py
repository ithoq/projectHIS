#-*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 >.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'IDS HR Roster',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
Employee Roster Management
======================================

    """,
    'author':'IDS Infotech Ltd.',
    'website':'http://idsil.com',
    'depends': ['hr'],
    'init_xml': [],
    'update_xml': [
        'view/hr_roster_view.xml',
    ],
    'test': [
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}
