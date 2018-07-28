# -*- coding: utf-8 -*-
##############################################################################
#
#    IDS Infotech Ltd.
#    Copyright (C) 2004-2010 Tiny SPRL (<http://idsil.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    'name': 'IDS HR Timesheets',
    'version': '1.0',
    'category': 'Human Resources',
    'sequence': 23,   
    'author': 'Satya',
    'website': 'http://www.idsil.com',
    'images': ['images/hr_timesheet_lines.jpeg'],
    'depends': ['ids_emp','hr_timesheet','hr_timesheet_sheet'],
    'data': [        
        'views/timesheet_view.xml',
        'views/hr_timesheets_workflow.xml',
        'views/schedule.xml',
        'ids_timesheet_report.xml',
        'wizard/timesheet_weekly_report.xml',
        'wizard/ids_timesheet_wizard.xml',
        'wizard/timesheet_attendance_analysis.xml',
		'views/project_sequence_view.xml',
       # 'timesheet_report.xml'

    ],    
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
