from django.shortcuts import render_to_response
from django.template.context import RequestContext

from scielomanager.journalmanager.forms import *
from scielomanager.editormanager import models
from scielomanager.journalmanager import models as jmmodels

AUTHZ_REDIRECT_URL = '/accounts/unauthorized/'


def journal_index(request):
    """
    Retrieve the editor Journals list
    """

    journals = models.User.objects.filter(user=request.user)

    return render_to_response(
        'editormanager/journal_list.html',
        {
            'journals': journals
        },
        context_instance=RequestContext(request)
    )
