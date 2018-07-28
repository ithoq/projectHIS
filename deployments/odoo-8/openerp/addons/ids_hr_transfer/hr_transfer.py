#-*- coding:utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class hr_transfer(osv.Model):

    
    _name = 'ids.hr.department.transfer'
    _description = 'Departmental Transfer'
    
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    def _get_employee_info(self, cr, uid, ids, name, args, context=None):
        """Getting the required employee information automatically. """      
        result = {}
        src_id = ''
        src_department= ''
        src_grade = ''
        src_division = ''
        src_location = ''
        src_reporting = ''
        
        if not ids:
            return []
        
        for self_obj_new in self.browse(cr, uid, ids, context=context):
             
            emp_info = self.pool.get('hr.employee').read(cr, SUPERUSER_ID, [self_obj_new.employee_id.id], ['job_id','department_id','grade_id','division','office_location','parent_id'])                
                        
            if emp_info:                
                src_id = emp_info[0]['job_id'][1]
                src_department = emp_info[0]['department_id'][1]
                src_grade = emp_info[0]['grade_id'][1]
                src_division = emp_info[0]['division'][1]
                src_location = emp_info[0]['office_location'][1]
                src_reporting = emp_info[0]['parent_id'][1]
                #result = dict.fromkeys(ids[self_obj_new.id], {'emp_code': emp_code, 'department_id': department_id, 'job_id': job_id, 'joining_date': joining_date, 'confirmation_date': confirmation_date, 'confirmation_status': confirmation_status})
                result[self_obj_new.id] = {'src_id': src_id, 'src_department': src_department, 'src_grade': src_grade, 'src_division': src_division, 'src_location': src_location, 'src_reporting': src_reporting}
               
        return result 
    
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True, readonly=True,
                               states={'draft': [('readonly',False)]}, domain="[('working_status', '!=', 'exit')]"),
        'src_id': fields.many2one('hr.job','Current Position'),
        'dst_id': fields.many2one('hr.job', 'New Position', readonly=True,
                               states={'draft': [('readonly',False)]}),
        'src_department': fields.many2one('hr.department','Current Department'),
        'dst_department': fields.many2one('hr.department', 'New Department', readonly=True,
                               states={'draft': [('readonly',False)]}),       
        'src_grade': fields.many2one('ids.employee.grade','Current Grade'),  
        'dst_grade': fields.many2one('ids.employee.grade', 'New Grade', readonly=True,
                               states={'draft': [('readonly',False)]}),
        'src_division': fields.many2one('division','Current Division'),  
        'dst_division': fields.many2one('division', 'New Division', readonly=True,
                               states={'draft': [('readonly',False)]}),
        'src_location': fields.many2one('office.location','Current Location'),  
        'dst_location': fields.many2one('office.location', 'New Location', readonly=True,
                               states={'draft': [('readonly',False)]}),
        'src_reporting': fields.many2one('hr.employee','Current Reporting Manager'),  
        'dst_reporting': fields.many2one('hr.employee', 'New Reporting Manager', readonly=True,
                               states={'draft': [('readonly',False)]}),   
        'emp_code': fields.related('employee_id', 'emp_code', type='char',
                                            relation='hr.employee', string='Employee Code',
                                            store=True, readonly=True),       
        'date': fields.date('Effective Date', required=True, readonly=True,
                            states={'draft': [('readonly',False)]}),
        'remarks': fields.text('Note', readonly=True,
                               states={'draft': [('readonly',False)]}),
        'flag':fields.boolean('Flag'),
        'state': fields.selection([
                                   ('draft', 'Draft'),
                                   ('confirm', 'Confirmed'),
                                   ('pending', 'Pending'),
                                   ('done', 'Done'),
                                   ('cancel', 'Cancelled'),
                                  ],
                                  'State', readonly=True),
    }
    
    _rec_name = 'date'
    
    _defaults = {
        'state': 'draft',
        'flag':False,
    }
    
    _track = {
        'state': {
            'ids_hr_transfer.mt_alert_xfer_confirmed': lambda self, cr,uid, obj, ctx=None: obj['state'] == 'confirm',
            'ids_hr_transfer.mt_alert_xfer_pending': lambda self, cr,uid, obj, ctx=None: obj['state'] == 'pending',
            'ids_hr_transfer.mt_alert_xfer_done': lambda self, cr,uid, obj, ctx=None: obj['state'] == 'done',
        },
    }
    
    def create(self, cr, uid, vals, context=None):
        """Constraint- One can create its own transfer. """
        if vals.get('employee_id'):
            ee = self.pool.get('hr.employee').browse(cr, uid, vals.get('employee_id'), context=context)            
            user_id = ee.user_id.id
            
            if user_id == uid:
                raise osv.except_osv(_('Warning!'), _('You cannot initiate your transfer.'))            
            
        res=super(hr_transfer, self).create(cr, uid, vals)
        self.write(cr,uid,res,{'flag':True})
        return res
    
    def _needaction_domain_get(self, cr, uid, context=None):
        
        users_obj = self.pool.get('res.users')
        
        domain = []
        if users_obj.has_group(cr, uid, 'base.group_hr_manager'):
            domain = [('state','=','confirm')]
            return domain
        
        return False
    
    def unlink(self, cr, uid, ids, context=None):
        
        for xfer in self.browse(cr, uid, ids, context=context):
            if xfer.state not in ['draft']:
                raise osv.except_osv(_('Unable to Delete Transfer!'),
                                     _('Transfer has been initiated. Either cancel the transfer or create another transfer to undo it.'))
        
        return super(hr_transfer, self).unlink(cr, uid, ids, context=context)
    
    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        """Gets associated fields in hr.employee on change of employee_id. """
        vals={}       
        if employee_id:    
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context=context)
            src_id = employee.job_id.id
            src_department = employee.department_id.id
            src_grade = employee.grade_id.id
            src_division = employee.division.id
            src_location = employee.office_location.id
            src_reporting = employee.parent_id.id
            vals = {
                    'src_id':src_id,
                    'src_department':src_department,
                    'src_grade':src_grade,
                    'src_division':src_division,
                    'src_location':src_location,
                    'src_reporting':src_reporting,
                    }
        res = {'value': vals}           
        return res
    
    def effective_date_in_future(self, cr, uid, ids, context=None):
        
        today = datetime.now().date()
        for xfer in self.browse(cr, uid, ids, context=context):
            effective_date = datetime.strptime(xfer.date, DEFAULT_SERVER_DATE_FORMAT).date()
            if effective_date <= today:
                return False
        
        return True
    
    def _check_state(self, cr, uid, contract_id, effective_date, context=None):
        
        contract_obj = self.pool.get('hr.contract')
        data = contract_obj.read(cr, uid, contract_id, ['state', 'date_end'], context=context)
        
        if data['state'] not in ['trial', 'trial_ending', 'open', 'contract_ending']:
            raise osv.except_osv(_('Warning!'), _('The current state of the contract does not permit changes.'))
        
        if data.get('date_end', False) and data['date_end'] != '':
            dContractEnd = datetime.strptime(data['date_end'], DEFAULT_SERVER_DATE_FORMAT)
            dEffective = datetime.strptime(effective_date, DEFAULT_SERVER_DATE_FORMAT)
            if dEffective >= dContractEnd:
                raise osv.except_osv(_('Warning!'), _('The contract end date is on or before the effective date of the transfer.'))
        
        return True
    
    def transfer_contract(self, cr, uid, contract_id, job_id, xfer_id, effective_date, context=None):
        
        contract_obj = self.pool.get('hr.contract')

        # Copy the contract and adjust start/end dates, job id, etc. accordingly.
        #
        default = {
            'job_id':job_id,
            'date_start': effective_date,
            'name': False,
            'state': False,
            'message_ids': False,
            'trial_date_start': False,
            'trial_date_end': False,
        }
        data = contract_obj.copy_data(cr, uid, contract_id, default=default, context=context)
        
        c_id = contract_obj.create(cr, uid, data, context=context)
        if c_id:
            vals = {}
            wkf = netsvc.LocalService('workflow')
            
            # Set the new contract to the appropriate state
            wkf.trg_validate(uid, 'hr.contract', c_id, 'signal_confirm', cr)
            
            # Terminate the current contract (and trigger appropriate state change)
            vals['date_end'] = datetime.strptime(effective_date, '%Y-%m-%d').date() + relativedelta(days= -1)
            contract_obj.write(cr, uid, contract_id, vals, context=context)
            wkf.trg_validate(uid, 'hr.contract', contract_id, 'signal_done', cr)
            
            # Link to the new contract
            self.pool.get('hr.department.transfer').write(cr, uid, xfer_id, {'dst_contract_id': c_id},
                                                          context=context)
        
        return
    
    def state_confirm(self, cr, uid, ids, context=None):
        """Workflow initited. """
        self._check_validate(cr, uid, ids, context=context)
        for xfer in self.browse(cr, uid, ids, context=context):
            #self._check_state(cr, uid, xfer.src_contract_id.id, xfer.date, context=context)
            self.write(cr, uid, xfer.id, {'state': 'confirm'}, context=context)
        
        return True
    
    def state_done(self, cr, uid, ids, context=None):
        
        employee_obj = self.pool.get('hr.employee')
        user_obj = self.pool.get('res.users')
        today = datetime.now().date()
        
        for xfer in self.browse(cr, uid, ids, context=context):
            
            if datetime.strptime(xfer.date, DEFAULT_SERVER_DATE_FORMAT).date() <= today:
                #self._check_state(cr, uid, xfer.src_contract_id.id, xfer.date, context=context)
                employee_obj.write(cr, SUPERUSER_ID, xfer.employee_id.id, {'grade_id': xfer.dst_grade.id,'office_location': xfer.dst_location.id,'parent_id': xfer.dst_reporting.id,'division': xfer.dst_division.id,'job_id': xfer.dst_id.id,'department_id': xfer.dst_department.id}, context=context)
                #self.transfer_contract(cr, uid, xfer.src_contract_id.id, xfer.dst_id.id,                                       xfer.id, xfer.date, context=context)
                user_obj.write(cr, SUPERUSER_ID, xfer.employee_id.user_id.id, {'location_id': xfer.dst_location.id,'division_id': xfer.dst_division.id}, context=context)
                self.write(cr, uid, xfer.id, {'state': 'done'}, context=context)
            else:
                return False
        
        return True
    
    def try_pending_department_transfers(self, cr, uid, context=None):
        """Completes pending departmental transfers. Called from the scheduler."""
        
        xfer_obj = self.pool.get('ids.hr.department.transfer')
        today = datetime.now().date()
        xfer_ids = xfer_obj.search(cr, uid, [
                                             ('state', '=', 'pending'),
                                             ('date', '<=', today.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                                            ], context=context)
        
        wkf = netsvc.LocalService('workflow')
        [wkf.trg_validate(uid, 'ids.hr.department.transfer', xfer.id, 'signal_done', cr) for xfer in self.browse(cr, uid, xfer_ids, context=context)]
        
        return True
    
    def _check_validate(self, cr, uid, ids, context=None):
        
        users_obj = self.pool.get('res.users')
        
        for transfer in self.browse(cr, uid, ids, context=context):
            if transfer.employee_id.user_id.id == uid:
                raise osv.except_osv(_('Warning!'), _('You cannot confirm your transfer.'))
        return