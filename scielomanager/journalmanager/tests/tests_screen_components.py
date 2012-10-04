# coding:utf-8
"""
Use this module to write functional tests for the screen components, only!
"""
from django_webtest import WebTest
from django.core.urlresolvers import reverse
from django_factory_boy import auth

from journalmanager.tests import modelfactories


HASH_FOR_123 = 'sha1$93d45$5f366b56ce0444bfea0f5634c7ce8248508c9799'


class CollectionsSelectorTests(WebTest):

    def test_auto_define_a_collection_as_default_when_it_is_the_unique(self):
        user = auth.UserF(is_active=True)

        collection = modelfactories.CollectionFactory.create()
        collection.add_user(user)

        page = self.app.get(reverse('index'), user=user)
        self.assertTrue(collection.name in page)
        # TODO: Test if the collection if marked as active

    def test_toggle_active_collection_unavailable_for_users_with_a_single_collection(self):
        user = auth.UserF(is_active=True)

        collection = modelfactories.CollectionFactory.create()
        collection.add_user(user)

        page = self.app.get(reverse('index'), user=user)
        self.assertNotIn('toggle_active_collection', page)

    def test_toggle_active_collection_available_for_users_with_many_collections(self):
        user = auth.UserF(is_active=True)

        collection = modelfactories.CollectionFactory.create(name='Brasil')
        collection.make_default_to_user(user)
        collection2 = modelfactories.CollectionFactory.create(name='Chile')
        collection2.add_user(user)

        page = self.app.get(reverse('index'), user=user)

        self.assertIn('Activate', page)
        # TODO: Test if the Activate buttom is related to the Chile collection