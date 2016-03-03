# coding: utf-8
import os
from datetime import date

from django.core.management import setup_environ
from django.core import exceptions

try:
    from scielomanager import settings
except ImportError:
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    BASE_PATH_APP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scielomanager'))
    from sys import path
    path.append(BASE_PATH)
    path.append(BASE_PATH_APP)

    import settings

setup_environ(settings)

from django.db.models import Q
from journalmanager.models import *
from django.contrib.auth.models import User
from journalmanager.models import *

import choices

logger = logging.getLogger(__name__)


def _config_logging(logging_level='INFO', logging_file=None):

    allowed_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.setLevel(allowed_levels.get(logging_level, 'INFO'))

    if logging_file:
        hl = logging.FileHandler(logging_file, mode='a')
    else:
        hl = logging.StreamHandler()

    hl.setFormatter(formatter)
    hl.setLevel(allowed_levels.get(logging_level, 'INFO'))

    logger.addHandler(hl)

    return logger


class Catalog(object):

    def __init__(self, collection, user=None):
        """
        data must be a Xylose object
        """
        self.user = User.objects.get(pk=1) if user is None else user
        try:
            self.collection = Collection.objects.get(acronym=collection)
        except:
            raise ValueError('Collection do no exists: %s' % collection)

    def _load_journal_mission(self, journal, missions):
        from sectionimport import LANG_DICT as lang_dict

        for language, description in missions.items():
            mission = JournalMission()
            language = Language.objects.get_or_create(
                iso_code=language,
                name=choices.LANG_DICT.get(language, '###NOT FOUND###'))[0]
            mission.language = language
            mission.description = description
            journal.missions.add(mission)

    def _load_journal_subject_areas(self, journal, areas):

        for area in areas:
            try:
                studyarea = StudyArea.objects.get(study_area=area)
            except:
                logger.warning('Invalid study area (%s) for the journal (%s), nothing was assigned' % (
                    area, journal.title)
                )

            journal.study_areas.add(studyarea)

    def _load_journal_textlanguage(self, journal, langs):
        for i in langs:
            language = Language.objects.get_or_create(
                iso_code=i,
                name=choices.LANG_DICT.get(i, '###NOT FOUND###'))[0]

            journal.languages.add(language)

    def _load_journal_abstractlanguage(self, journal, langs):
        for i in langs:
            language = Language.objects.get_or_create(
                iso_code=i,
                name=choices.LANG_DICT.get(i, '###NOT FOUND###'))[0]

            journal.abstract_keyword_languages.add(language)

    def _load_journal_status_history(self, journal, status_history, user):

        for st_date, status, reason in status_history:

            if len(st_date) == 4:
                st_date += '-01-01'

            if len(st_date) == 7:
                st_date += '-01'

            defaults = {
                'created_by': user,
            }

            try:
                timeline = JournalTimeline.objects.get_or_create(
                    journal=journal,
                    collection=self.collection,
                    since=st_date,
                    status=status,
                    defaults=defaults)[0]
            except exceptions.ValidationError:
                logger.warning('Invalid timeline (%s) for the journal (%s), nothing was assigned' % (
                    ', '.join([date, status, reason]), journal.title)
                )

        try:
            membership = Membership.objects.get_or_create(
                journal=journal,
                collection=self.collection,
                since=st_date,
                status=status,
                defaults=defaults
            )
        except:
            logger.warning('Invalid membership (%s) for the journal (%s), nothing was assigned' % (
                ', '.join([date, status, reason]), journal.title)
            )

        """
        models.Membership sempre replica o registro salvo para o
        JournalTimeline. No momento da importação esse comportamento é
        indesejado, para contorná-lo é realizada a exclusão dos registros
        inseridos verificando a data da execução da importação
        """
        JournalTimeline.objects.filter(
            since__month=date.today().month,
            since__year=date.today().year).delete()

    def _load_journal_other_titles(self, journal, data):

        for title in data.other_titles or []:
            title = JournalTitle()
            title.title = title
            title.category = 'other'
            journal.other_titles.add(title)

        # NLM/Medline Title
        if data.title_nlm:
            title = JournalTitle()
            title.title = data.title_nlm
            title.category = 'abbrev_nlm'
            journal.other_titles.add(title)

    def _load_journal_use_license(self, journal, permission):

        use_license = UseLicense.objects.get_or_create(
            license_code=permission['id'].upper())[0]

        if 'text' in permission and permission['text']:
            use_license.disclaimer = permission['text']

        if 'url' in permission and permission['url']:
            use_license.reference_url = permission['url']

        use_license.save()

        journal.use_license = use_license

    def _load_journal_sponsor(self, journal, data):
        """
        Function: load_sponsor
        Retorna um objeto Sponsor() caso a gravação do mesmo em banco de dados for concluida
        """

        for sponsor in data.sponsors or []:

            db_sponsor = Sponsor.objects.get_or_create(name=sponsor)[0]
            db_sponsor.collections.add(self.collection)
            db_sponsor.save()
            journal.sponsor.add(db_sponsor)

    def _post_save_journal(self, journal, data):
        """
        Este método existe para dados que só podem ser associados a um
        journal já persisitido, como por exemplo métodos que dependem da
        existência de um PK definido.
        """

        journal.created = data.creation_date
        journal.updated = data.update_date
        self._load_journal_textlanguage(journal, data.languages or [])
        self._load_journal_abstractlanguage(journal, data.abstract_languages or [])
        self._load_journal_subject_areas(journal, data.subject_areas or [])
        self._load_journal_mission(journal, data.mission or [])
        self._load_journal_other_titles(journal, data)
        self._load_journal_status_history(journal, data.status_history or [], self.user)
        self._load_journal_use_license(journal, data.permissions)
        self._load_journal_sponsor(journal, data)

        journal.save()

    def load_journal(self, data):
        logger.info('Importing Journal')

        journal = Journal()

        journal.creator_id = self.user.pk
        journal.collection = self.collection
        journal.scielo_issn = 'electronic' if data.scielo_issn == data.electronic_issn else 'print'
        journal.print_issn = data.print_issn or ''
        journal.eletronic_issn = data.electronic_issn or ''
        journal.title = data.title or ''
        journal.title_iso = data.abbreviated_iso_title or ''
        journal.short_title = data.abbreviated_title or ''
        journal.medline_title = data.title_nlm or ''
        journal.acronym = data.acronym
        journal.subject_descriptors = '\n'.join(data.subject_descriptors or [])
        journal.index_coverage = '\n'.join(data.subject_descriptors or [])
        journal.copyrighter = data.copyrighter or ''
        journal.init_year = data.first_year or ''
        journal.init_vol = data.first_volume or ''
        journal.init_num = data.first_number or ''
        journal.final_year = data.last_year or ''
        journal.final_vol = data.last_volume or ''
        journal.final_num = data.last_number or ''
        journal.cnn_code = data.cnn_code or ''
        journal.frequency = data.periodicity[0] if data.periodicity else ''
        journal.url_online_submission = data.submission_url or ''
        journal.url_journal = data.institutional_url or data.url() or ''
        journal.pub_status = data.current_status or ''
        journal.editorial_standard = data.editorial_standard[0] if data.editorial_standard else ''
        journal.ctrl_vocabulary = data.controlled_vocabulary[0] if data.controlled_vocabulary else ''
        journal.pub_level = data.publication_level[0] if data.publication_level else ''
        journal.secs_code = data.secs_code or ''
        journal.publisher_name = '; '.join(data.publisher_name) if data.publisher_name else ''
        journal.publisher_country = data.publisher_country[0] if data.publisher_country else ''
        journal.publisher_state = data.publisher_state or ''
        journal.publisher_city = data.publisher_city or ''
        journal.editor_address = data.editor_address or ''
        journal.editor_email = data.editor_email or ''
        journal.is_indexed_scie = data.is_indexed_in_scie
        journal.is_indexed_ssci = data.is_indexed_in_ssci
        journal.is_indexed_aehci = data.is_indexed_in_ahci

        journal.save(force_insert=True)

        self._post_save_journal(journal, data)

        logger.info('Journal (%s) created' % data.title)

        return journal

    def _load_issue_sections(self, issue, data):
        pass

    def _load_issue_titles(self, issue, data):
        pass

    def _load_issue_use_license(self, issue, permission):

        use_license = UseLicense.objects.get_or_create(
            license_code=permission['id'].upper())[0]

        if 'text' in permission and permission['text']:
            use_license.disclaimer = permission['text']

        if 'url' in permission and permission['url']:
            use_license.reference_url = permission['url']

        use_license.save()

        issue.use_license = use_license

    def _post_save_issue(self, issue, data):

        issue.created = data.creation_date
        issue.updated = data.update_date
        #self._load_issue_titles(issue, data)
        #self._load_issue_sections(issue, data)
        if data.permissions:
            self._load_issue_use_license(issue, data.permissions)

        issue.save()

    def load_issue(self, data):
        try:
            journal = Journal.objects.get(
                Q(print_issn=data.journal.scielo_issn) |
                Q(eletronic_issn=data.journal.scielo_issn))
            logger.info('Journal already exists, skiping journal creation')
        except:
            logger.info('Journal do no exists, creating journal')
            journal = self.load_journal(data.journal)

        logger.info('Importing Issue (%s)' % (data.label))

        spe = 'spe' if data.type == 'special' else None
        suppl = ' '.join([
                data.supplement_volume or '',
                data.supplement_number or ''
            ]).strip() if data.type == 'supplement' else None

        try:
            issue = Issue.objects.get(
                journal=journal,
                publication_year=data.publication_date[:4],
                volume=data.volume or '',
                number=data.number or '',
                type=data.type,
                spe_text=spe,
                suppl_text=suppl)
            logger.info('Issue already exists, skiping issue creation')
            return
        except:
            logger.info('Issue do not exists, creating issue')

        issue = Issue()
        issue.journal = journal
        issue.publication_year = data.publication_date[:4]
        issue.volume = data.volume or ''
        issue.number = data.number or ''
        issue.type = data.type
        if data.type == 'special' and spe:
            issue.spe_text = spe
        elif data.type == 'supplement' and suppl:
            issue.suppl_text = suppl
        issue.order = data.order
        issue.is_press_release = data.is_press_release
        issue.total_documents = data.total_documents or 0
        issue.publication_start_month = data.start_month or 0
        issue.publication_end_month = data.end_month or 0
        issue.is_marked_up = data.is_marked_up
        issue.ctrl_vocabulary = data.controlled_vocabulary
        issue.editorial_standard = data.editorial_standard

        try:
            issue.save(force_insert=True)
        except django.db.utils.DatabaseError:
            import pdb; pdb.set_trace()


        self._post_save_issue(issue, data)

        logger.info('Issue (%s) created' % (data.label))
