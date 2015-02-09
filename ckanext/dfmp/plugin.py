import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.logic import side_effect_free
from datetime import datetime
from time import sleep

import logging as l

class DFMPPlugin(plugins.SingletonPlugin):
  plugins.implements(plugins.IActions)
  inProgress = 0
  def get_actions(self):
      return {
        'user_add_asset': user_add_asset,
        'user_get_assets': user_get_assets,
        'user_create_with_dataset': user_create_with_dataset,
        'user_remove_asset':user_remove_asset,
      }




def user_add_asset(context, data_dict):
  """Add new asset"""
  orgs = toolkit.get_action('organization_list_for_user')(context, {'permission':'read'}) 

  owner_id    = orgs[0]['id']     if orgs else context['auth_user_obj'].id
  owner_name  = orgs[0]['title']  if orgs else context['auth_user_obj'].name

  while DFMPPlugin.inProgress:
    sleep(.1)
  DFMPPlugin.inProgress += 1

  resource = toolkit.get_action('resource_create')(context, {
                                                  'package_id' : _get_assets_name(context),
                                                  'url':data_dict['url'],
                                                  'name':data_dict['name'],
                                                  'size':data_dict['size'],
                                                  'mimetype':data_dict['type']
                                                })


  DFMPPlugin.inProgress -= 1
  datastore = toolkit.get_action('datastore_create')(context,{
                                          'force':True,
                                          'resource_id': resource['id'],
                                          'fields':[
                                            {'id':'date', 'type':'text'},
                                            {'id':'creator_id', 'type':'text'},
                                            {'id':'creator_name', 'type':'text'},
                                            {'id':'owner_id', 'type':'text'},
                                            {'id':'owner_name', 'type':'text'},
                                            {'id':'license_id', 'type':'text'},
                                            {'id':'type', 'type':'text'},
                                          ],
                                          'records': [
                                            {
                                              'creator_id':context['auth_user_obj'].id,
                                              'creator_name': context['auth_user_obj'].name,
                                              'date':datetime.now().isoformat(),
                                              'owner_id':owner_id,
                                              'owner_name':owner_name,
                                              'license_id':data_dict['license'],
                                              'type':data_dict['type'],
                                              'thumb':data_dict['thumbnailUrl'],
                                            }
                                          ]
                                     })
  return resource.update(datastore=datastore)




@side_effect_free
def user_get_assets(context, data_dict):
  """Get all assets of user"""
  try:
    dataset = toolkit.get_action('package_show')(context,{'id' : _get_assets_name(context) })
    for resource in dataset['resources']:
      resource.update( datastore = toolkit.get_action('datastore_search')(context,{'resource_id': resource['id']}).get('records') )
    return dataset
  except toolkit.ObjectNotFound, e:
    return {}

def user_remove_asset(context, data_dict):
  """Remove one asset"""
  try:
    result = toolkit.get_action('datastore_delete')(context,{
                                          'force':True,
                                          'resource_id': data_dict['id'],
                                          })
  except toolkit.ObjectNotFound:
    pass
  toolkit.get_action('resource_delete')(context,{'id': data_dict['id']})


def user_create_with_dataset(context, data_dict):
  user = toolkit.get_action('user_create')(context, data_dict)

  try:
    toolkit.get_action('package_create')(context, { 'name' : _get_assets_name(context) })
  except toolkit.ValidationError:
    pass

  return user


def _get_assets_name(context):
  return 'dfmp_assets_'+context['auth_user_obj'].name

  