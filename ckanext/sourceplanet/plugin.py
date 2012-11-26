import os
from logging import getLogger
from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IDatasetForm, IConfigurer, IRoutes
from ckan.logic.schema import package_form_schema
from ckan.lib.base import c, model
from ckan.lib import base
from ckan.lib.navl import dictization_functions
from ckan.lib.navl.validators import ignore_missing, not_empty
from ckan import authz
from ckan import logic
from pylons import config, request, response
import logic.schema
from ckan.logic.converters import convert_to_extras, convert_from_extras
from ckan.lib.plugins import DefaultDatasetForm

log = getLogger(__name__)
dataset_types = ['product', 'project']

class SourceplanetDatasetForm(SingletonPlugin, DefaultDatasetForm):
    implements(IDatasetForm, inherit=True)
    implements(IConfigurer, inherit=True)
    implements(IRoutes, inherit=True)

    def update_config(self, config):
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        template_dir = os.path.join(
            rootdir, 'ckanext', 'sourceplanet', 'theme', 'templates')
        config['extra_template_paths'] = ','.join(
            [template_dir, config.get('extra_template_paths', '')])
	config['extra_public_paths'] = os.path.join(rootdir, 'ckanext', 'sourceplanet', 'theme', 'public')
	config['licenses_group_url'] = 'http://dev.morelab.deusto.es/sourceplanet/osi_list.json'
	config['ckan.site_logo'] = 'http://dev.morelab.deusto.es/sourceplanet/img/sourceplanet.png'
	config['ckan.site_description'] = 'SourcePlanet'
	config['ckan.site_title'] = 'SourcePlanet'

    def package_form(self):
        return 'forms/new_package_form.html'

    def new_template(self):
        return 'forms/new.html'

    def comments_template(self):
        return 'forms/comments.html'

    def search_template(self):
        return 'forms/search.html'

    def read_template(self):
        return 'forms/read.html'

    def history_template(self):
        return 'forms/history.html'

    def is_fallback(self):
        return True

    def package_types(self):
        return dataset_types

    def setup_template_variables(self, context, data_dict=None):
	DefaultDatasetForm.setup_template_variables(self, context, data_dict)

        # SourcePlanet customization
        route = request.environ.get('CKAN_CURRENT_URL')
        c.dataset_type = route.split('/')[1]

    def form_to_db_schema(self):
	schema = DefaultDatasetForm.form_to_db_schema(self)

        # SourcePlanet customization
        schema.update({
            'dataset_type': [ignore_missing, unicode],
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
            'dataset_type': [ignore_missing]
        })

	log.info("vamossssss")
	
        return schema

    def before_map(self, map):
        # Configuration to get working the extension
        for type in dataset_types:
            with map.submapper(controller='package') as m:
                m.connect('/%s' % type, action='search')
                m.connect('/%s/{action}' % type,
                          requirements=dict(action='|'.join([
                                                            'list',
                                                            'new',
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
