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
from pylons import config, request
import logic.schema
from ckan.logic.converters import convert_to_extras, convert_from_extras

log = getLogger(__name__)
dataset_types = ['product', 'project']


class SourceplanetPlugin(SingletonPlugin):
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
        log.info("Templaterlll!!!")
        # Configuration to get working the extension
        authz_fn = logic.get_action('group_list_authz')
        c.groups_authz = authz_fn(context, data_dict)
        data_dict.update({'available_only': True})

        c.groups_available = authz_fn(context, data_dict)

        c.licences = [('', '')] + base.model.Package.get_license_options()
        c.is_sysadmin = authz.Authorizer().is_sysadmin(c.user)

        if c.pkg:
            c.related_count = c.pkg.related_count

        context_pkg = context.get('package', None)
        pkg = context_pkg or c.pkg
        if pkg:
            try:
                if not context_pkg:
                    context['package'] = pkg
                logic.check_access('package_change_state', context)
                c.auth_for_change_state = True
            except logic.NotAuthorized:
                c.auth_for_change_state = False

        # SourcePlanet customization
        route = request.environ.get('CKAN_CURRENT_URL')
        c.dataset_type = route.split('/')[1]

        def form_to_db_schema(self):
            schema = package_form_schema()

        '''
            # Configuration to get working the extension (not needed at this time)
            schema = options.get('context', {}).get('schema', None)
            if schema:
                return schema

            if options.get('api'):
                if options.get('type') == 'create':
                    return self.form_to_db_schema_api_create()
                else:
                    assert options.get('type') == 'update'
                    return self.form_to_db_schema_api_update()
            else:
                return self.form_to_db_schema()
        '''

        # SourcePlanet customization
        schema.update({
            'dataset_type': [ignore_missing, unicode],
        })

        return schema

    def db_to_form_schema(self):
        schema = package_form_schema()

        # Configuration to get working the extension
        schema.update({
            'id': [ignore_missing, unicode]
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

        return schema

    def check_data_dict(self, data_dict, schema=None):
        # Configuration to get working the extension
        surplus_keys_schema = ['__extras', '__junk', 'state', 'groups',
                               'extras_validation', 'save', 'return_to',
                               'resources', 'type']

        if not schema:
            schema = self.form_to_db_schema()
        schema_keys = schema.keys()
        keys_in_schema = set(schema_keys) - set(surplus_keys_schema)

        missing_keys = keys_in_schema - set(data_dict.keys())
        if missing_keys:
            log.info('Incorrect form fields posted, missing %s' % missing_keys)
            raise dictization_functions.DataError(data_dict)

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
