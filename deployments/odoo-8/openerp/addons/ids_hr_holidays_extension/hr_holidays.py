# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, osv
import time
from datetime import date
from openerp.tools.translate import _
from pytz import timezone, utc
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_is_zero, float_compare

class ids_hr_holidays_club(osv.osv):
    
    _name = 'ids.hr.holidays.club'
    _description = "Club Leaves"           
    _columns = {
                'with_holiday_id': fields.many2one('hr.holidays.status', 'With Holiday Type', required=True),
                'holiday_status_id':fields.many2one('hr.holidays.status', 'Leaves', invisible=True)
                }
    _sql_constraints = [('club_leave_check','UNIQUE(holiday_status_id, with_holiday_id)','Entry Already Exist.'),
                        ('club_self_leave_check','CHECK(with_holiday_id != holiday_status_id)','Invalid Entry.')]

class hr_holidays_status(osv.Model):
    
    _inherit = 'hr.holidays.status'
    _name = 'hr.holidays.status'
    
    _columns = {
        'ex_rest_days': fields.boolean('Exclude Rest Days/ Weekend Days', help="If enabled, the employee's day off is skipped in leave days calculation."),
        'ex_public_holidays': fields.boolean('Exclude Public Holidays', help="If enabled, public holidays are skipped in leave days calculation."),
        'code': fields.char('Code', size=100, required=True),
        'one_time_apply_limit': fields.float('One Time Maximum Avail Limit', required=True, help='Means how many leaves can be availed at one time. -1.00 means unlimited.'),
        'yearly_apply_limit': fields.float('Yearly Maximum Avail Limit', required=True, help='Means how many leaves can be availed in a single year. -1.00 means unlimited.'),
        'yearly_allocation_limit': fields.float('Yearly Maximum Leave Allocation', required=True, help='Means how many leaves can be allocated in a single year. -1.00 means unlimited.'),
        'leave_lapse_limit': fields.float('Leave Lapse Limit?', required=True, help='Means how many leaves will get lapsed if not availed in a single calendar year. -1 means leave will not get lapsed.'),
        'yearly_apply_times': fields.integer('How many times can be applied?', required=True, help='Means how many times in a year you can apply for leave. -1 means unlimited.'),
        'carry_forward': fields.boolean('Can be carried forward?', help='Remaining leave at end of the year can be carried forward or not.'),
        'accumulated_limit': fields.float('Accumulated limit?', help='In case leaves can be carried forward, upto what limit they will be accumulated. -1 means unlimited'),
        'can_be_clubbed': fields.boolean('Can be clubbed with other leaves?'),
        'holiday_club_ids':fields.one2many('ids.hr.holidays.club','holiday_status_id', 'Leave Club Details'),
        'holiday_allowed_ids':fields.one2many('ids.hr.holidays.allowed','holiday_status_id', 'Leave allowed Details', invisible=True),
        'employee_confirmed': fields.boolean('Employee should be confirmed?'),
        'allowed_in_notice_period': fields.boolean('Allowed in notice period?'),
        'allowed_for_half_day': fields.boolean('Allowed for half day?'),
        'encashable': fields.boolean('Can be encashed?'),
        ## Added By Satya
        'day_before_apply': fields.float('Days Before Apply', required=True, help='Means how many days before leave can be apply.'),
   
    }
    
    _defaults = {
        'one_time_apply_limit':-1.00,
        'yearly_apply_limit':-1.00,
        'leave_lapse_limit':-1.00,
        'yearly_apply_times':-1,
        'accumulated_limit':-1.00,
        'day_before_apply':-1.00       
    } 
    
    def frange(self, x, y, jump):
        while x <= y:
            yield x
            x += jump
              
    
    def create(self, cr, uid, vals, context=None):
        """ Override to avoid automatic functionality """
        holiday_status_id = super(hr_holidays_status, self).create(cr, uid, vals, context=context)       
        
        #Add new records to table
        if vals.get('one_time_apply_limit', False):
            if (vals['one_time_apply_limit'] > 0):
                if vals.get('allowed_for_half_day', False): 
                    allowed_leaves = self.frange(0.5,vals['one_time_apply_limit'],0.5)
                    allowed_leaves_list = ["%g" % x for x in allowed_leaves]
                else:
                    allowed_leaves = self.frange(1,vals['one_time_apply_limit'],1)
                    allowed_leaves_list = ["%g" % x for x in allowed_leaves]
            else:
                allowed_leaves_list = [0]
        else:
            allowed_leaves_list = [0] 
        
        #insert allowed leave values in ids_hr_holidays_allowed for each leave type     
        for allowed_value in allowed_leaves_list:                
            self.pool.get('ids.hr.holidays.allowed').create(cr, uid, {'number_of_days_temp_temp':allowed_value,'holiday_status_id': holiday_status_id, }, context=context)
        
        return holiday_status_id
        
    def unlink(self, cr, uid, ids, context=None):        
        
        ids_hr_holidays_allowed_object = self.pool.get('ids.hr.holidays.allowed')
        for hol_status_id in ids:    
            allowed_leave_ids = []
            allowed_leave_ids = ids_hr_holidays_allowed_object.search(cr, uid, [('holiday_status_id','=', hol_status_id)])
            ids_hr_holidays_allowed_object.unlink(cr, uid, allowed_leave_ids, context=context)        
                      
        return super(hr_holidays_status, self).unlink(cr, uid, ids, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        
        holiday_status_id = ids[0]
        if super(hr_holidays_status, self).write(cr, uid, ids, vals, context=context):
        
            #delete present records from table
            ids_hr_holidays_allowed_object = self.pool.get('ids.hr.holidays.allowed')
            allowed_leave_ids = ids_hr_holidays_allowed_object.search(cr, uid, [('holiday_status_id','=', holiday_status_id)])
            ids_hr_holidays_allowed_object.unlink(cr, uid, allowed_leave_ids, context=context)                                               
            
            values = {}
            #Add new records to table
            for holiday_status in self.pool.get('hr.holidays.status').browse(cr, uid, [holiday_status_id], context=context):
                if holiday_status.name:
                    values['one_time_apply_limit'] = holiday_status.one_time_apply_limit 
                    values['allowed_for_half_day'] = holiday_status.allowed_for_half_day
                    values['one_time_apply_limit'] = holiday_status.one_time_apply_limit          
            
            if values.get('one_time_apply_limit', False):
                if (values['one_time_apply_limit'] > 0):
                    if values.get('allowed_for_half_day', False): 
                        allowed_leaves = self.frange(0.5,values['one_time_apply_limit'],0.5)
                        allowed_leaves_list = ["%g" % x for x in allowed_leaves]
                    else:
                        allowed_leaves = self.frange(1,values['one_time_apply_limit'],1)
                        allowed_leaves_list = ["%g" % x for x in allowed_leaves]
                else:
                    allowed_leaves_list = [0]
            else:
                allowed_leaves_list = [0] 
            
            #insert allowed leave values in ids_hr_holidays_allowed for each leave type     
            for allowed_value in allowed_leaves_list:                
                self.pool.get('ids.hr.holidays.allowed').create(cr, uid, {'number_of_days_temp_temp':allowed_value,'holiday_status_id': holiday_status_id}, context=context)
    
            return True
        else:
            return False                                      
    
    def allocate_holidays_new_joinee(self, cr, uid, emp_code, context=None): 
        
        NEW_JOINEE_PL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 0
        NEW_JOINEE_CL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 3.0
        NEW_JOINEE_SL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 3.0

        PL_HOLIDAY_CODE = 'PL'       
        CL_HOLIDAY_CODE = 'CL'   
        SL_HOLIDAY_CODE = 'SL'
                
        obj_res_holiday_status = self.pool.get('hr.holidays.status')
        obj_res_employee = self.pool.get('hr.employee') 
        
        leaves_arr = []
        
        leaves_arr.append((PL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':NEW_JOINEE_PL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE}))
        leaves_arr.append((CL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':NEW_JOINEE_CL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE}))
        leaves_arr.append((SL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':NEW_JOINEE_SL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE}))
        
        new_leaves_arr = dict(leaves_arr)
        
        for leaves in new_leaves_arr:           
            emp_holiday_list  = []
            holiday_code      = leaves
            holiday_title     = new_leaves_arr[leaves]['title']
            holiday_status_id = new_leaves_arr[leaves]['holiday_status_id']
            max_holidays      = new_leaves_arr[leaves]['max_holidays']       
        
            if max_holidays:
                obj_res_holiday_status_obj = obj_res_holiday_status.search(cr, uid, [('code','=', holiday_code)])
            
                if len(obj_res_holiday_status_obj):
                    holiday_status_id = obj_res_holiday_status_obj[0]
                    for holiday_status in obj_res_holiday_status.browse(cr, uid, [holiday_status_id], context=context):
                        if holiday_status.name:
                            holiday_title = holiday_status.name           
                
                if holiday_status_id:
                    #Code to allocate PL automatically
                    obj_res_employee_ids = obj_res_employee.search(cr, uid, [('emp_code','=', emp_code)])
                    #Create dictionary with employee id as key and number of holidays as value
                    for employee_id in obj_res_employee_ids:
                          emp_holiday_list.append((employee_id,max_holidays))
                
                    self._allocate_holidays(cr, uid, holiday_status_id, holiday_title, emp_holiday_list, context=context) 
                    
        return True
    
    def allocate_holidays_on_confirmation(self, cr, uid, emp_id, context=None):       
        
        employee_id = emp_id
        
        #Start Code : Code to find current cycle    
        first_cycle_date  = time.strftime('%Y-06-30')
        second_cycle_date = time.strftime('%Y-12-31')
        current_date      = time.strftime('%Y-%m-%d')
        current_cycle_date = ''
        
        if (current_date > first_cycle_date):
            current_cycle_date = second_cycle_date
        else:
            current_cycle_date = first_cycle_date
        #End Code : Code to find current cycle
    
                    
        
        #Start Code : Code to find required employee information  
        obj_emp = self.pool.get('hr.employee')       
        employee_record = obj_emp.browse(cr, uid, [employee_id])
        joining_date      = ''
        confirmation_date = ''
        for employee in employee_record:
            joining_date = employee.joining_date
            confirmation_date = employee.confirmation_date        
        #Start Code : Code to find required employee information  
        
        
        
        
        PL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 9.0
        CL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 3.0
        SL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 3.0

        PL_HOLIDAY_CODE = 'PL'       
        CL_HOLIDAY_CODE = 'CL'   
        SL_HOLIDAY_CODE = 'SL'
                
        
        
        #Start Code : Calculate PL to allocate 
        
        d1 = datetime.strptime(joining_date, DEFAULT_SERVER_DATE_FORMAT).date()
        d2 = datetime.strptime(confirmation_date, DEFAULT_SERVER_DATE_FORMAT).date()
        r = relativedelta(d2,d1)
        pl_months = r.months
        pl_days = r.days
               
        pl_leaves_per_month = PL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE/6
        pl_max_leaves_to_allocate = 0
        
        pl_month_leaves =  (pl_months*pl_leaves_per_month)
        pl_day_leaves = 0
        if (pl_days > 25):
            pl_day_leaves = pl_leaves_per_month
        elif (pl_days > 15):
            pl_day_leaves = (pl_leaves_per_month/3)*2
        elif (pl_days > 5):
            pl_day_leaves = pl_leaves_per_month/3    
        
        pl_max_leaves_to_allocate = pl_month_leaves + pl_day_leaves
        #End Code : Calculate PL to allocate
        
        #Start Code : Calculate CL to allocate
        
        d1 = datetime.strptime(confirmation_date, DEFAULT_SERVER_DATE_FORMAT).date()
        d2 = datetime.strptime(current_cycle_date, DEFAULT_SERVER_DATE_FORMAT).date()
        r = relativedelta(d2,d1)
        cl_months = r.months
        cl_days = r.days
                
        cl_leaves_per_month = CL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE/6
        cl_max_leaves_to_allocate = 0
        
        cl_month_leaves =  (cl_months*cl_leaves_per_month)
        cl_day_leaves = 0
        if (cl_days >= 15):
            cl_day_leaves = cl_leaves_per_month
                    
        cl_max_leaves_to_allocate = cl_month_leaves + cl_day_leaves
        #End Code : Calculate CL to allocate        
        
        #Start Code : Calculate SL to allocate
        sl_max_leaves_to_allocate = cl_max_leaves_to_allocate
        #End Code : Calculate CL to allocate
        
        obj_res_holiday_status = self.pool.get('hr.holidays.status')
        
        leaves_arr = []
        leaves_arr.append((PL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':pl_max_leaves_to_allocate}))
        leaves_arr.append((CL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':cl_max_leaves_to_allocate}))
        leaves_arr.append((SL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':sl_max_leaves_to_allocate}))
        
        new_leaves_arr = dict(leaves_arr)        
        
        for leaves in new_leaves_arr:           
            emp_holiday_list  = []
            holiday_code      = leaves
            holiday_title     = new_leaves_arr[leaves]['title']
            holiday_status_id = new_leaves_arr[leaves]['holiday_status_id']
            max_holidays      = new_leaves_arr[leaves]['max_holidays']       
            
            if max_holidays:
                obj_res_holiday_status_obj = obj_res_holiday_status.search(cr, uid, [('code','=', holiday_code)])
                
                if len(obj_res_holiday_status_obj):
                    holiday_status_id = obj_res_holiday_status_obj[0]
                    for holiday_status in obj_res_holiday_status.browse(cr, uid, [holiday_status_id], context=context):
                        if holiday_status.name:
                            holiday_title = holiday_status.name           
                
                if holiday_status_id:                    
                    emp_holiday_list.append((employee_id,max_holidays))                
                    self._allocate_holidays(cr, uid, holiday_status_id, holiday_title, emp_holiday_list, context=context) 
                    
        return True
                    
    def allocate_holidays(self, cr, uid, context=None):       
        
        PL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 9.0
        CL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 3.0
        SL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE = 3.0

        PL_HOLIDAY_CODE = 'PL'       
        CL_HOLIDAY_CODE = 'CL'   
        SL_HOLIDAY_CODE = 'SL'
                
        obj_res_holiday_status = self.pool.get('hr.holidays.status')
        obj_res_employee = self.pool.get('hr.employee') 
        
        leaves_arr = []
        
        leaves_arr.append((PL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':PL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE}))
        leaves_arr.append((CL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':CL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE}))
        leaves_arr.append((SL_HOLIDAY_CODE,{'title':'', 'holiday_status_id':0, 'max_holidays':SL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE}))
        
        new_leaves_arr = dict(leaves_arr)
        
        
        for leaves in new_leaves_arr:           
            emp_holiday_list  = []
            holiday_code      = leaves
            holiday_title     = new_leaves_arr[leaves]['title']
            holiday_status_id = new_leaves_arr[leaves]['holiday_status_id']
            max_holidays      = new_leaves_arr[leaves]['max_holidays']       
            
            if max_holidays:
                obj_res_holiday_status_obj = obj_res_holiday_status.search(cr, uid, [('code','=', holiday_code)])
                
                if len(obj_res_holiday_status_obj):
                    holiday_status_id = obj_res_holiday_status_obj[0]
                    for holiday_status in obj_res_holiday_status.browse(cr, uid, [holiday_status_id], context=context):
                        if holiday_status.name:
                            holiday_title = holiday_status.name           
                
                if holiday_status_id:
                    #Code to allocate PL automatically
                    obj_res_employee_ids = obj_res_employee.search(cr, uid, [('emp_code','!=', False),('active','=', 1),('confirmation_status','=', 'confirmed')])
                    #Create dictionary with employee id as key and number of holidays as value
                    for employee_id in obj_res_employee_ids:
                          
                        #Start Code: Calculate PL from confirmation date to next cycle date
                        if (holiday_code == PL_HOLIDAY_CODE):
                            employee_record = obj_emp.browse(cr, uid, [employee_id])                              
                            confirmation_date = ''
                            for employee in employee_record:                                  
                                confirmation_date = employee.confirmation_date
                            
                            #Start Code : Code to find current cycle    
                            first_cycle_date  = time.strftime('%Y-06-30')
                            second_cycle_date = time.strftime('%Y-12-31')
                            current_date      = time.strftime('%Y-%m-%d')
                            current_cycle_date = ''
                              
                            if (current_date > first_cycle_date):
                                current_cycle_date = second_cycle_date
                            else:
                                current_cycle_date = first_cycle_date                   
                            #End Code : Code to find current cycle
                            
                            d1 = datetime.strptime(confirmation_date, DEFAULT_SERVER_DATE_FORMAT).date()
                            d2 = datetime.strptime(current_cycle_date, DEFAULT_SERVER_DATE_FORMAT).date()
                            r = relativedelta(d2,d1)
                            pl_months = r.months
                            pl_days = r.days
                            
                            if (((pl_months == 6) & (pl_days == 0))):
                                max_holidays = 0
                            elif (pl_months < 6):
                                pl_leaves_per_month = PL_MAX_NUMBER_OF_HOLIDAYS_TO_ALLOCATE/6                                
                                pl_month_leaves =  (pl_months*pl_leaves_per_month)
                                pl_day_leaves = 0
                                if (pl_days > 25):
                                    pl_day_leaves = pl_leaves_per_month
                                elif (pl_days > 15):
                                    pl_day_leaves = (pl_leaves_per_month/3)*2
                                elif (pl_days > 5):
                                    pl_day_leaves = pl_leaves_per_month/3    
                                
                                max_holidays = pl_month_leaves + pl_day_leaves
                         
                        #End Code: Calculate PL from confirmation date to next cycle date
                          
                        emp_holiday_list.append((employee_id,max_holidays))
                
                    self._allocate_holidays(cr, uid, holiday_status_id, holiday_title, emp_holiday_list, context=context) 
        return True
    
    def _allocate_holidays(self, cr, uid, holiday_status_id, holiday_name, list_holidays, context=None):   
        
        #array to store allocated id's so that we can change the status as per workflow
        allocated_holiday_ids = []     
        
        #get manager id            
        ids2 = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)])
        manager = ids2 and ids2[0] or False
        
        employee_leave_dict = dict(list_holidays)
        for emp_id in employee_leave_dict:
            
            if employee_leave_dict[emp_id] > 0:
                #Allocate & Approve PL to all active and confirmed employees            
                vals = {
                    'holiday_status_id': holiday_status_id,
                    'employee_id':emp_id,
                    'name': holiday_name,
                    'number_of_days_temp': float(employee_leave_dict[emp_id]),
                    'number_of_days': employee_leave_dict[emp_id],
                    'holiday_type': 'employee',
                    'state': 'confirm',
                    'manager_id':manager,
                    'type': 'add'
                }
                allocated_holiday_ids.append(self.pool.get('hr.holidays').create(cr, uid, vals, context=context))
            
        for allocated_holiday_id in allocated_holiday_ids:
            self.pool.get('hr.holidays').write(cr, uid, [allocated_holiday_id], {'state':'validate'})    
        
        return True

class ids_hr_holidays_allowed(osv.osv):
    
    _name = 'ids.hr.holidays.allowed'
    _description = "Allowed Partial Leaves"           
    _columns = {
                'number_of_days_temp_temp': fields.float('Holiday Value', required=True),
                'holiday_status_id':fields.many2one('hr.holidays.status', 'Leaves')
                }
    _rec_name = 'number_of_days_temp_temp'
    
class hr_holidays(osv.osv):
    
    
    def frange(x, y, jump):
        while x <= y:
            yield x
            x += jump
            
    allowed_leaves = frange(0.5,100.0,0.5)
    allowed_leaves_list = [(("%g" % x),("%g" % x)) for x in allowed_leaves]
    
    _name = 'hr.holidays'
    _inherit = ['hr.holidays', 'ir.needaction_mixin']
    
    _columns = {
        'real_days': fields.float('Total Days', digits=(16, 1), readonly=True, states={'draft':[('readonly',False)],},),
        'rest_days': fields.float('Rest Days/Weekend Days', digits=(16, 1),readonly=True, states={'draft':[('readonly',False)],},),
        'public_holiday_days': fields.float('Public Holidays', digits=(16, 1), readonly=True, states={'draft':[('readonly',False)],},),  
        'holiday_allowed_value' : fields.selection(allowed_leaves_list,'Days Requested',readonly=True, states={'draft':[('readonly',False)],},),
        'date_from_temp': fields.date('Start Date', select=True),
        'date_to_temp': fields.date('End Date', select=True),
        'first_half_temp': fields.boolean('First Half of Date From'),
        'second_half_temp': fields.boolean('First Half of Date To'),
        'return_date': fields.char('Return Date', size=32),
        'division_id':fields.many2one('division', 'Division'),
        'year': fields.integer('Year'),
        'active': fields.boolean('Active')
    }

    def _employee_get(self, cr, uid, context=None):
        """Get default employee from user_id. """
        if context == None:
            context = {}
        
        # If the user didn't enter from "My Leaves" don't pre-populate Employee field
        import logging
        _l = logging.getLogger(__name__)
        _l.warning('context: %s', context)
        if not context.get('search_default_my_leaves', False):
            return False
        
        ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)], context=context)
        if ids:
            return ids[0]
        return False

    def _days_get(self, cr, uid, context=None):
        """Get total number of days from date_from and date_to. """
        if context == None:
            context = {}
        
        date_from = context.get('default_date_from')
        date_to = context.get('default_date_to')
        if date_from and date_to:
            delta = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT)
            return (delta.days and delta.days or 1)
        return False
    
    def _default_allocate_year(self, cr, uid, context=None):  
        today =datetime.today()      
        return (today.year)
    
    _defaults = {
        'employee_id': _employee_get,
        'number_of_days_temp': _days_get,
        'year': _default_allocate_year,
        'active' : True
    }

    _order = 'date_from asc, type desc'
    
    def _needaction_domain_get(self, cr, uid, context=None):
        
        users_obj = self.pool.get('res.users')
        domain = []
        
        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            domain = [('state', 'in', ['draft', 'confirm'])]
            return domain
        
        elif users_obj.has_group(cr, uid, 'ids_hr_holidays_extension.group_hr_leave'):
            domain = [('state', 'in', ['confirm']), ('employee_id.user_id', '!=', uid)]
            return domain
        
        return False  
    
    def onchange_employee_id(self, cr, uid, ids, division_id,employee_id, context=None):
        """Get division on change of empployee_id. """
        emp_id=self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
        division_id=emp_id.division
        res= {'value': {'division_id': division_id}}
        return res
    
    def onchange_holiday_type(self, cr, uid, ids, holiday_status_id, holiday_allowed_value, context=None):
        """Get total allocated leaves for applying leaves. """        
        if (holiday_allowed_value and holiday_status_id):
            
            one_time_apply_limit = 0
            allowed_for_half_day = False
            allowed_value = float(holiday_allowed_value)
            name = ''
            
            hr_holidays_status_obj = self.pool.get('hr.holidays.status')
            for holiday_status in hr_holidays_status_obj.browse(cr, uid, [holiday_status_id], context=context):
                if holiday_status.name:
                    one_time_apply_limit = holiday_status.one_time_apply_limit
                    allowed_for_half_day = holiday_status.allowed_for_half_day
                    name = holiday_status.name
            
            if ((one_time_apply_limit != -1) and float(holiday_allowed_value) > one_time_apply_limit):
                raise osv.except_osv(_('Warning:'),
                                     _('You can apply maximum %s leaves') % (one_time_apply_limit))                
                
            elif ((not(allowed_for_half_day)) and (allowed_value%1 == 0.5)):
                raise osv.except_osv(_('Warning:'),
                                     _('Partial leave is not allowed for %s type of leaves') % (name))         
        return True

    def onchange_enddate(self, cr, uid, ids, employee_id,
                         date_from, date_to, holiday_status_id, no_days, first_half, second_half, context=None):
        if (date_from !=False and date_to !=False): 
            ee_obj = self.pool.get('hr.employee')
            holiday_obj = self.pool.get('ids.hr.public.holidays')
            #sched_tpl_obj = self.pool.get('hr.schedule.template')
            res = {'value': {'return_date': False}}
    
            if holiday_status_id:
                hs_data = self.pool.get('hr.holidays.status').read(cr, uid, holiday_status_id,
                                                                   ['ex_rest_days', 'ex_public_holidays'],
                                                                   context=context)
            else:
                hs_data = {}
                
            ex_rd = hs_data.get('ex_rest_days', False)
            ex_ph = hs_data.get('ex_public_holidays', False)
    
            rest_days = []
            
            if ex_rd:
                #Code for Rest days based on schedule module...commented by Shiv
                '''
                ee = ee_obj.browse(cr, uid, employee_id, context=context)
                if ee.contract_id and ee.contract_id.schedule_template_id:
                    rest_days = sched_tpl_obj.get_rest_days(cr, uid,
                                                            ee.contract_id.schedule_template_id.id,
                                                            context=context)'''
    
            dt = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
                        
            return_date_change = False
            real_days = 0
            d1 = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT).date()
            d2 = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT).date()
            r = relativedelta(d2,d1)
            real_days = r.days+1.0
            
            if second_half:
                real_days = real_days - 0.5
                
            if (first_half and second_half and (date_to == date_from)):
                return_date = dt + timedelta(days= +1)
                real_days = 1.0
            elif first_half:
                return_date = dt
                real_days = real_days - 0.5
            else:
                return_date = dt + timedelta(days= +1)
            
            
            
            
            count_days = no_days
            
            ph_days = 0
            r_days = 0        
                
            while (return_date.weekday() in rest_days and ex_rd) or (holiday_obj.is_public_holiday(cr, uid, return_date.date(), context=context) and ex_ph):
                if holiday_obj.is_public_holiday(cr, uid, return_date.date(), context=context): 
                    ph_days += 1
                elif return_date.weekday() in rest_days: 
                    r_days += 1
                            
                return_date += timedelta(days=1)
                real_days += 1
                return_date_change = True
            
            if (first_half and second_half and (date_to == date_from)):
                res['value']['return_date'] = return_date.strftime('%B %d, %Y')
            elif first_half and (not(return_date_change)):
                res['value']['return_date'] = return_date.strftime('%B %d, %Y')+' Second Half'
            else:
                res['value']['return_date'] = return_date.strftime('%B %d, %Y')
                 
            res['value']['rest_days'] = r_days
            res['value']['public_holiday_days'] = ph_days
            res['value']['real_days'] = real_days         
                                    
            return res
        
        else:
            return False
   
    def _check_applied_leaves(self, cr, uid, vals, context=None):
        first_half = second_half = []
        reset=0
        if vals.get('date_from_temp', False):        
            calculate_no_days = 0
            date_from   = vals['date_from_temp']
            date_to     = vals['date_to_temp']
            second_half = vals['second_half_temp']
            first_half  = vals['first_half_temp']
            no_days     = float(vals['holiday_allowed_value'])
            leave_start_time = ''
            leave_end_time = ''        
            
            '''for leave_id in self.pool.get('ids.hr.holidays.allowed').browse(cr, uid, [vals['holiday_allowed_id']], context=context):
                if leave_id.number_of_days_temp_temp:
                    no_days = leave_id.number_of_days_temp_temp'''           
            
            self.onchange_holiday_type(cr, uid, vals, vals['holiday_status_id'], no_days, context)            
              
            date_from = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
            date_to   = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
            
            if (date_from == date_to):
                if ((first_half and second_half) or (not(first_half) and not(second_half))):                
                    calculate_no_days = 1.0
                    leave_start_time = datetime.strptime((date_from.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 09:00:01'),  DEFAULT_SERVER_DATETIME_FORMAT)                
                    leave_end_time = datetime.strptime(date_to.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 18:00:00',  DEFAULT_SERVER_DATETIME_FORMAT) 
                elif first_half:
                    calculate_no_days = 0.5
                    leave_start_time = datetime.strptime(date_from.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 09:00:01',  DEFAULT_SERVER_DATETIME_FORMAT)
                    leave_end_time = datetime.strptime(date_to.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 13:00:00',  DEFAULT_SERVER_DATETIME_FORMAT)    
                elif second_half:
                    calculate_no_days = 0.5
                    leave_start_time = datetime.strptime(date_from.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 14:00:01',  DEFAULT_SERVER_DATETIME_FORMAT)
                    leave_end_time = datetime.strptime(date_to.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 18:00:00',  DEFAULT_SERVER_DATETIME_FORMAT)                     
            else:
                d1 = datetime.strptime(vals['date_from_temp'], DEFAULT_SERVER_DATE_FORMAT).date()
                d2 = datetime.strptime(vals['date_to_temp'], DEFAULT_SERVER_DATE_FORMAT).date()
                r = relativedelta(d2,d1)
                reset = d2-d1
                leave_start_time = datetime.strptime(date_from.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 09:00:01',  DEFAULT_SERVER_DATETIME_FORMAT)
                leave_end_time = datetime.strptime(date_to.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 18:00:00',  DEFAULT_SERVER_DATETIME_FORMAT) 
                calculate_no_days = (reset.days)+1.0
                if second_half:
                    calculate_no_days = calculate_no_days-0.5
                    leave_start_time = datetime.strptime(date_from.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 09:00:01',  DEFAULT_SERVER_DATETIME_FORMAT)
                    leave_end_time = datetime.strptime(date_to.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 13:00:00',  DEFAULT_SERVER_DATETIME_FORMAT) 
                if first_half:
                    calculate_no_days = calculate_no_days-0.5
                    leave_start_time = datetime.strptime(date_from.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 14:00:01',  DEFAULT_SERVER_DATETIME_FORMAT)
                    leave_end_time = datetime.strptime(date_to.strftime(DEFAULT_SERVER_DATE_FORMAT) +' 18:00:00',  DEFAULT_SERVER_DATETIME_FORMAT)    
            
            if no_days != calculate_no_days:
                raise osv.except_osv(_('Warning'), _('Days Requested and Duration Provided are not matching.'))
            else:
                vals['date_from'] = leave_start_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                vals['date_to'] = leave_end_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)         
                vals['number_of_days_temp'] = calculate_no_days           
                return vals
                
    def create(self, cr, uid, vals, context=None):
        self._check_applied_leaves(cr, uid, vals, context=None)
                
        type_obj=  self.pool.get('hr.holidays.status')
        att_obj = self.pool.get('hr.attendance')
        cur_date=time.strftime("%Y-%m-%d")
        type_id = vals['holiday_status_id']
        type_ids = type_obj.search(cr, uid, [('id', '=', type_id)])
        type_records = type_obj.browse(cr, uid, type_ids, context=context)
        if vals.get('date_from_temp',False):
            dt_temp=datetime.strptime(vals['date_from_temp'], '%Y-%m-%d').date()
            c_date=datetime.strptime(cur_date, '%Y-%m-%d').date()
            dt_temp1=(date.today().replace(day=dt_temp.day,month=dt_temp.month,year=dt_temp.year))
            cur_date1=(date.today().replace(day=c_date.day,month=c_date.month,year=c_date.year))
            difference=(dt_temp1 - cur_date1).days
            if vals['date_from_temp']>cur_date and type_records.code == 'SL':
                raise osv.except_osv(_('Warning'),
                                         _('You can not apply future Sick Leave'))
            if type_records.day_before_apply>difference and type_records.day_before_apply<>-1:
                raise osv.except_osv(_('Warning'),
                                         _('You can not apply Leave. Please contact to HR.'))
        # # # # # # # # #         
        if vals.get('date_from', False) and vals.get('date_to', False) and (not vals.get('type', False) or vals.get('type', 'x') == 'remove') and vals.get('holiday_type', 'x') == 'employee':
            att_date_from=datetime.strptime(vals['date_from'], '%Y-%m-%d %H:%M:%S')
            att_date_to=datetime.strptime(vals['date_to'], '%Y-%m-%d %H:%M:%S')
            date_from =att_date_from - timedelta(hours=5,minutes=30)
            date_to =att_date_to - timedelta(hours=5,minutes=30)
            atten_time1 = datetime.strftime(date_from,'%Y-%m-%d %H:%M:%S')
            atten_time2 = datetime.strftime(date_to,'%Y-%m-%d %H:%M:%S')
            att_ids = att_obj.search(cr, uid, [('employee_id', '=', vals['employee_id']),
                                               ('name', '>=', atten_time1),
                                               ('name', '<=', atten_time2)],
                                     context=context)
            #if len(att_ids) > 0:
                #raise osv.except_osv(_('Warning'),
                # _('There is already one or more attendance records for the date you have chosen.'))
                
        # # # # # # # # #  
        #if vals.get('type') == 'add':  
            #allocate=list1=[]
            #now=datetime.now()
            #year=now.year
            #if vals['year']==year:
                #cr.execute("select sum(number_of_days) from hr_holidays where type='add' and employee_id =%s and state='validate' and holiday_status_id=%s and year=%s",(vals['employee_id'], type_id,vals['year']))
                #allocate= cr.fetchall()
                #if allocate<>[(None,)]:
                    #list1 = [int(i[0]) for i in allocate]
                    #data1 = list1[0]
                    #total = data1 + vals['number_of_days_temp']
                    #if total> type_records.yearly_allocation_limit:
                            #raise osv.except_osv(_('Warning'),_('You can not allocate leaves more than yearly limit'))
            
        # # # # # # # # #      
        url="http://ids-erp.idsil.loc:8069/web"
 
        if vals.get('type') == 'remove':
            leave=self.browse(cr, uid, vals, context=context)
            employee=self.pool.get('hr.employee').search(cr,uid,[('id','=',vals['employee_id'])])
            emp_data=self.pool.get('hr.employee').browse(cr, uid, employee, context=context)
            status_id=self.pool.get('hr.holidays.status').search(cr,uid,[('id','=',vals['holiday_status_id'])])
            status=self.pool.get('hr.holidays.status').browse(cr, uid, status_id, context=context)
            values = {
            'subject': 'Leave Request By'+' '+ emp_data.name,
            'body_html': emp_data.name+' '+ 'requested for'+' '+vals['holiday_allowed_value']+' '+'day/s'+' '+status.name+' '+'for your approval from '+vals['date_from_temp']+ ' to ' +vals['date_to_temp']+'.'+'<br/><br/><br/>Kindly do not reply.<br/>---This is auto generated email---<br/>Regards:<br/>ERP HR Team<br/>IDS Infotech LTD.<br/>Url:'+url,
            'email_to': emp_data.parent_id.work_email,
            'email_from': 'info.openerp@idsil.com',
              }
            #---------------------------------------------------------------
            mail_obj = self.pool.get('mail.mail') 
            msg_id = mail_obj.create(cr, uid, values, context=context) 
            if msg_id: 
                mail_obj.send(cr, uid, [msg_id], context=context) 
            

        return super(hr_holidays, self).create(cr, uid, vals, context=context)
    def holidays_confirm(self, cr, uid, ids, context=None):
        # changed on 07 july 2017
#         for record in self.browse(cr, uid, ids, context=context):
#             if record.employee_id and record.employee_id.parent_id and record.employee_id.parent_id.user_id:
#                 self.message_subscribe_users(cr, uid, [record.id], user_ids=[record.employee_id.parent_id.user_id.id], context=context)
        return self.write(cr, uid, ids, {'state': 'confirm'})

    def holidays_first_validate(self, cr, uid, ids, context=None):
        
        self._check_validate(cr, uid, ids, context=context)
        return super(hr_holidays, self).holidays_first_validate(cr, uid, ids, context=context)
    
    def holidays_validate(self, cr, uid, ids, context=None):
        
        self._check_validate(cr, uid, ids, context=context)
        return super(hr_holidays, self).holidays_validate(cr, uid, ids, context=context)
    
    def holidays_validate_multi(self, cr, uid, ids, context=None):
        
        for leave in self.browse(cr, uid, ids, context=context):
            cr.execute("update hr_holidays set state='validate' where id=%s"%(leave.id));
            if leave.employee_id.user_id.id == uid:
                raise osv.except_osv(_('Warning!'), _('You cannot approve your own Leave:\nEmployee: %s') % (leave.employee_id.name))
        return True
    
    def holidays_refuse(self, cr, uid, ids, context=None):
        leave=self.browse(cr, uid, ids, context=context)
        url="http://ids-erp.idsil.loc:8069/web"
        if leave.type == 'remove':
            employee=self.pool.get('hr.employee').search(cr,uid,[('id','=',leave.employee_id.id)])
            emp_data=self.pool.get('hr.employee').browse(cr, uid, employee, context=context)
            values = {
            'subject': 'Leave Request Status'+' ['+ leave.holiday_status_id.name+ ' ]',
            'body_html': 'Your'+' '+leave.holiday_allowed_value+' '+'day/s'+' '+leave.holiday_status_id.name+' '+'Request is Refused.<br/><br/><br/>Kindly do not reply.<br/>---This is auto generated email---<br/>Regards:<br/>ERP HR Team<br/>IDS Infotech LTD.<br/>Url:'+url,
            'email_to': emp_data.work_email,
            'email_from': 'info.openerp@idsil.com',
              }
            #---------------------------------------------------------------
            mail_obj = self.pool.get('mail.mail') 
            msg_id = mail_obj.create(cr, uid, values, context=context) 
            if msg_id: 
                mail_obj.send(cr, uid, [msg_id], context=context) 
        
        return super(hr_holidays, self).holidays_refuse(cr, uid, ids, context=context)
    
    def _check_validate(self, cr, uid, ids, context=None):
        leave=self.browse(cr, uid, ids, context=context)
        users_obj = self.pool.get('res.users')
        
        if not users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            for leave in self.browse(cr, uid, ids, context=context):
                if leave.type=='remove':
                    ### Added By Satya
                    cur_date=time.strftime("%Y-%m-%d")
                    dt_temp=datetime.strptime(leave.date_from_temp, '%Y-%m-%d').date()
                    c_date=datetime.strptime(cur_date, '%Y-%m-%d').date()
                    dt_temp1=(date.today().replace(day=dt_temp.day,month=dt_temp.month,year=dt_temp.year))
                    cur_date1=(date.today().replace(day=c_date.day,month=c_date.month,year=c_date.year))
                    difference=(dt_temp1 - cur_date1).days
                    if difference<0 and leave.holiday_status_id.day_before_apply<>-1:
                        raise osv.except_osv(_('Warning!'), _('You cannot approve past leave:\nHoliday Type: %s\nEmployee: %s') % (leave.holiday_status_id.name, leave.employee_id.name))
                    ###################
                if leave.employee_id.user_id.id == uid:
                    raise osv.except_osv(_('Warning!'), _('You cannot approve your own leave:\nHoliday Type: %s\nEmployee: %s') % (leave.holiday_status_id.name, leave.employee_id.name))
        url="http://ids-erp.idsil.loc:8069/web"
        if leave.type == 'remove':
            employee=self.pool.get('hr.employee').search(cr,uid,[('id','=',leave.employee_id.id)])
            emp_data=self.pool.get('hr.employee').browse(cr, uid, employee, context=context)
            values = {
            'subject': 'Leave Request Status'+' ['+ leave.holiday_status_id.name+ ' ]',
            'body_html': 'Your'+' '+leave.holiday_allowed_value+' '+'day/s'+' '+leave.holiday_status_id.name+' '+'Request is Approved.<br/><br/><br/>Kindly do not reply.<br/>---This is auto generated email---<br/>Regards:<br/>ERP HR Team<br/>IDS Infotech LTD.<br/>Url:'+url,
            'email_to': emp_data.work_email,
            'email_from': 'info.openerp@idsil.com',
              }
            #---------------------------------------------------------------
            mail_obj = self.pool.get('mail.mail') 
            msg_id = mail_obj.create(cr, uid, values, context=context) 
            if msg_id: 
                mail_obj.send(cr, uid, [msg_id], context=context) 
                
        #if leave.type == 'add':
            #now=datetime.now()
            #year=now.year
            #type_obj=  self.pool.get('hr.holidays.status')
            #type_ids = type_obj.search(cr, uid, [('id', '=', leave.holiday_status_id.id)])
            #type_records = type_obj.browse(cr, uid, type_ids, context=context)
            #if leave.year==year:
                #cr.execute("select sum(number_of_days) from hr_holidays where year=%s and  type='add' and employee_id =%s and state='validate' and holiday_status_id=%s",(year,leave.employee_id.id, leave.holiday_status_id.id))
                #allocate= cr.fetchall()
                #if allocate<>[(None,)]:
                    #list1 = [int(i[0]) for i in allocate]
                    #data1 = list1[0]
                    #total = data1 + leave.number_of_days_temp
                    #if total> type_records.yearly_allocation_limit:
                            #raise osv.except_osv(_('Warning'),_('You can not allocate leaves more than yearly limit'))
                
        
        
        return
    ####################Scheduled action for Birthday leave allocation############
    def allocate_birthday_leave(self,cr,uid,context=None):
        """ Allocate birthday leave automatic """
        url="http://ids-erp.idsil.loc:8069/web"
        today = datetime.now()+ relativedelta(days=5)
        today_month_day = '%-' + today.strftime('%m') + '-' + today.strftime('%d')
        emp_ids = self.pool.get('hr.employee').search(cr, uid, [('birthday', 'like', today_month_day)])
        if emp_ids:
            for emp_id in self.pool.get('hr.employee').browse(cr, uid, emp_ids,context=context):
                values = {
                    'type':'add',
                    'state':'draft',
                    'employee_id': emp_id.id,
                    'holiday_status_id': 9,
                    'holiday_type': 'employee',
                    'number_of_days_temp': 1,
                    'name': 'birthday leave',
                    'department_id' : emp_id.department_id.id,
                    'year': 2018,
                    
                      }
                holiday_obj = self.pool.get('hr.holidays') 
                holiday_id = holiday_obj.create(cr, uid, values, context=context)
                values_mail = {
                'subject': 'Birthday Leave Allocation',
                'body_html': 'Your birthday leave is allocated.<br/><br/><br/>Kindly do not reply.<br/>---This is auto generated email---<br/>Regards:<br/>ERP HR Team<br/>IDS Infotech LTD.<br/>Url:'+url,
                'email_to': emp_id.work_email,
                'email_from': 'info.openerp@idsil.com',
                  }
                mail_obj = self.pool.get('mail.mail') 
                msg_id = mail_obj.create(cr, uid, values_mail, context=context) 
                if msg_id: 
                    mail_obj.send(cr, uid, [msg_id], context=context) 
        return True

class hr_attendance(osv.Model):
    
    _name = 'hr.attendance'
    _inherit = 'hr.attendance'
    
    def create(self, cr, uid, vals, context=None):
        
        if vals.get('name', False):
            lv_ids = self.pool.get('hr.holidays').search(cr, uid, [('employee_id', '=', vals['employee_id']),
                                                                   ('type', '=', 'remove'),
                                                                   ('date_from', '<=', vals['name']),
                                                                   ('date_to', '>=', vals['name']),
                                                                   ('state', 'not in', ['cancel', 'refuse'])],
                                                         context=context)
            if len(lv_ids) > 0:
                ee_data = self.pool.get('hr.employee').read(cr, uid, vals['employee_id'], ['name'],
                                                            context=context)
                #raise osv.except_osv(_('Warning'),
                                    # _('There is already one or more leaves recorded for the date you have chosen:\nEmployee: %s\nDate: %s' %(ee_data['name'], vals###['name'])))
        
        return super(hr_attendance, self).create(cr, uid, vals, context=context)        
    