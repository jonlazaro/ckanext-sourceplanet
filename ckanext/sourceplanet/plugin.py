import os
from sets import Set
from logging import getLogger
from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IDatasetForm, IConfigurer, IRoutes
from ckan.logic.schema import package_form_schema
from ckan.lib.base import c, model
from ckan.lib import base
from ckan.lib.navl import dictization_functions
from ckan.lib.navl.validators import ignore_missing, not_empty, ignore
from ckan import authz
from ckan import logic
from pylons import config, request, response
import logic.schema
from ckan.logic.converters import convert_to_extras, convert_from_extras
from ckan.lib.plugins import DefaultDatasetForm


from ckan.lib.navl.dictization_functions import unflatten
from ckan.logic import (tuplize_dict,
                        clean_dict,
                        parse_params,
                        flatten_to_string_key,
			get_action)

from load_data_model import load_data_model


log = getLogger(__name__)
dataset_types = ['product', 'project']

#Evaluation indicators
evaluation_model = {
    'name': [ignore_missing],
    'uri': [ignore_missing],
    'category': [ignore_missing],
    'dataset_type': [ignore_missing],
    'value': [ignore_missing], 
}

class SourceplanetDatasetForm(SingletonPlugin, DefaultDatasetForm):
    implements(IDatasetForm, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IRoutes, inherit=True)

    def update_config(self, config):
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))

	#New template dir
        template_dir = os.path.join(
            rootdir, 'ckanext', 'sourceplanet', 'theme', 'templates')
        config['extra_template_paths'] = ','.join(
            [template_dir, config.get('extra_template_paths', '')])

	#New public dir
	public_dir = os.path.join(rootdir, 'ckanext', 'sourceplanet', 'theme', 'public')
        config['extra_public_paths'] = ','.join(
            [public_dir, config.get('extra_public_paths', '')])

	#OSI licenses added
	config['licenses_group_url'] = 'file://' + os.path.join(public_dir, 'licenses', 'osi_list.json')

	#Basic customization
	config['ckan.site_logo'] = '/img/sourceplanet.png'
	config['ckan.site_description'] = 'Semantic Planet for Open Source'
	config['ckan.site_title'] = 'SourcePlanet'

    def package_form(self):
        return 'package/new_package_form.html'

    def new_template(self):
        return 'package/new.html'

    def comments_template(self):
        return 'package/comments.html'

    def search_template(self):
        return 'package/search.html'

    def read_template(self):
        return 'package/read.html'

    def history_template(self):
        return 'package/history.html'

    def is_fallback(self):
        return True

    def package_types(self):
        return dataset_types

    def setup_template_variables(self, context, data_dict=None):
	DefaultDatasetForm.setup_template_variables(self, context, data_dict)

        # SourcePlanet customization
        route = request.environ.get('CKAN_CURRENT_URL')
        c.dataset_type = route.split('/')[1]

	if 'evaluations' not in data_dict.keys(): #not c.pkg:
	    eval_list = []
            for eval in load_data_model():
                if eval['dataset_type'] == route.split('/')[1]:
                    eval_list.append(eval)

            c.evaluations = eval_list
	else:
	    c.evaluations = data_dict['evaluations']

    def form_to_db_schema(self):
	schema = DefaultDatasetForm.form_to_db_schema(self)

        schema.update({
            'dataset_type': [ignore_missing, unicode],
	    'evaluations': evaluation_model,
        })

	return schema

    def db_to_form_schema(self):
        schema = package_form_schema()

        # Configuration to get working the extension
        schema.update({
            'id': [ignore_missing, unicode],
            'isopen': [ignore_missing],
        })

        schema['groups'].update({
            'name': [not_empty, unicode],
            'title': [ignore_missing],
            'capacity': [ignore_missing, unicode]
        })

        # SourcePlanet customization
        schema.update({
            'dataset_type': [ignore_missing],
            'evaluations': evaluation_model,
        })

        return schema

    def check_data_dict(self, data_dict):
	data_dict['type'] = data_dict['dataset_type']

	DefaultDatasetForm.check_data_dict(self, data_dict)

    def before_map(self, map):
	map.connect('/licenses/osi_list.json', _static=True)

        # Configuration to get working the extension
        for type in dataset_types:
	    with map.submapper(controller='package') as m:
		m.connect('/%s' % type, action='search')
                m.connect('/%s/{action}' % type,
                          requirements=dict(action='|'.join([
                                                            'new',
							    'list',
                                                            'autocomplete',
                                                            'search'
                                                            ]))
                          )

                m.connect(
                    '/%s/{action}/{id}/{revision}' % type, action='read_ajax',
                    requirements=dict(action='|'.join([
                    'read',
                    'edit',
                    'authz',
                    'history',
                    ]))
                )

                m.connect('/%s/{action}/{id}' % type,
                          requirements=dict(action='|'.join([
                                                            'edit',
							    'new_metadata',
                                                            'new_resource',
                                                            'authz',
                                                            'history',
                                                            'read_ajax',
                                                            'history_ajax',
                                                            'followers',
                                                            'follow',
                                                            'unfollow',
                                                            'delete',
                                                            'api_data',
                                                            'editresources',
                                                            ]))
                          )
                m.connect('/%s/{id}.{format}' % type, action='read')
                m.connect('/%s/{id}' % type, action='read')
                m.connect('/%s/{id}/resource/{resource_id}' % type,
                          action='resource_read')
                m.connect('/%s/{id}/resource_delete/{resource_id}' % type,
                          action='resource_delete')
                m.connect('/%s/{id}/resource_edit/{resource_id}' % type,
                          action='resource_edit')
                m.connect('/%s/{id}/resource/{resource_id}/download' % type,
                          action='resource_download')
                m.connect('/%s/{id}/resource/{resource_id}/embed' % type,
                          action='resource_embedded_dataviewer')
                m.connect('/%s/{id}/resource/{resource_id}/viewer' % type,
                          action='resource_embedded_dataviewer', width="960", height="800")
                m.connect(
                    '/%s/{id}/resource/{resource_id}/preview/{preview_type}' % type,
                    action='resource_datapreview')
                m.connect('/search', action='search')

            with map.submapper(controller='related') as m:
                m.connect('related_new',
                          '/%s/{id}/related/new' % type, action='new')
                m.connect(
                    'related_edit', '/%s/{id}/related/edit/{related_id}' % type,
                    action='edit')
                m.connect(
                    'related_delete', '/%s/{id}/related/delete/{related_id}' % type,
                    action='delete')
                m.connect(
                    'related_list', '/%s/{id}/related' % type, action='list')

            with map.submapper(controller='api', path_prefix='/api{ver:/1|/2|}', ver='/1') as m:
                m.connect(
                    '/util/%s/autocomplete' % type, action='dataset_autocomplete',
                    conditions=dict(method=['GET']))
                m.connect(
                    '/util/%s/munge_name' % type, action='munge_package_name')
                m.connect('/util/%s/munge_title_to_name' % type,
                          action='munge_title_to_package_name')

            if config.get('ckan.datastore.enabled', False):
                with map.submapper(controller='datastore') as m:
                    m.connect('datastore_read_shortcut',
                              '/%s/{dataset}/resource/{id}/api{url:(/.*)?}' % type,
                              action='read', url='', conditions=dict(method=['GET']))
                    m.connect('datastore_write_shortcut',
                              '/%s/{dataset}/resource/{id}/api{url:(/.*)?}' % type,
                              action='write', url='', conditions=dict(method=['PUT', 'POST', 'DELETE']))

        return map
