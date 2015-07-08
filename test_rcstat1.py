import os
from web import flask_main
import unittest
import tempfile
import shutil
import time

class RcstatTestCase(unittest.TestCase):

    def setUp(self):
        ##enable slurm sacct command
        os.environ['PATH'] = '/curc/slurm/slurm/current/bin:${PATH}'
        os.environ['LD_LIBRARY_PATH'] = '/curc/slurm/slurm/current/lib:${LD_LIBRARY_PATH}'
        os.environ['MANPATH'] = 'curc/slurm/slurm/current/share/man${MANPATH}'
        os.environ['SLURM_ROOT'] = '/curc/slurm/slurm/current'
        os.environ['I_MPI_PMI_LIBRARY'] = '/curc/slurm/slurm/current/lib/libmpi.so'
        #start webapp
        flask_main.app.config['Testing'] = True
        self.app = flask_main.app.test_client()

    def tearDown(self):
        dirs_to_remove = [100, 101, 102, 103, 843833, 
                            843855, '100_1']
        for dir1 in dirs_to_remove:
            try:
                shutil.rmtree('web/static/job/{d}'.format(d=dir1))
            except OSError, e:
                pass

            try:
                os.unlink('sacct_output/{d}.txt'.format(d=dir1))
            except OSError, e:
                pass

            try:
                os.unlink('web/static/job/{d}.zip'.format(d=dir1))
            except OSError, e:
                pass


    def test_blank_input(self):
        rv = self.app.post('/graph_summary', data=dict(
            text=''), follow_redirects=True)
        assert 'is invalid. Please enter a valid Job ID.' in rv.data

    def test_negative_number_input(self):
        rv = self.app.post('/graph_summary', data=dict(
            text='-777777'), follow_redirects=True)
        assert 'is invalid. Please enter a valid Job ID.' in rv.data

    def test_too_long_input(self):
        rv = self.app.post('/graph_summary', data=dict(
            text='123456789'), follow_redirects=True)
        assert 'is invalid. Please enter a valid Job ID.' in rv.data

    def test_not_a_number_input(self):
        rv = self.app.post('/graph_summary', data=dict(
            text='asdh~!?'), follow_redirects=True)
        assert 'is invalid. Please enter a valid Job ID.' in rv.data

    def test_valid_input_no_job_input(self):
        '''Test a valid input that has no associated job'''
        rv = self.app.post('/graph_summary', data=dict(
            text='100'), follow_redirects=True)
        assert 'No job data found for' in rv.data

    def test_valid_input_no_job2_input(self):
        '''Test a valid input that has no associated job where slurm
        returns an Unknown start time'''
        rv = self.app.post('/graph_summary', data=dict(
            text='100_1'), follow_redirects=True)
        assert 'No job data found for' in rv.data

    def test_slurm_call_rate_limit(self):
        start = time.time()
        rv = self.app.post('/graph_summary', data=dict(
            text='101'), follow_redirects=True)
        rv = self.app.post('/graph_summary', data=dict(
            text='102'), follow_redirects=True)
        rv = self.app.post('/graph_summary', data=dict(
            text='103'), follow_redirects=True)
        # print rv.data
        assert time.time() - start >= 2

    def test_successful_submission(self):
        rv = self.app.post('/graph_summary', data=dict(
            text='843833'), follow_redirects=True)
        num_agg_images = flask_main.get_num_images(843833, 'agg', '')
        num_cpu_images = flask_main.get_num_images(843833, 'cpu', 'node')
        assert num_agg_images == 4
        assert num_cpu_images == 1

    def test_goto_url_directly(self):
        rv = self.app.post('/static/job/843833/avg', follow_redirects=True)
        num_avg_images = flask_main.get_num_images(843833, 'avg', '')
        assert num_avg_images == 4

    # def test_send_an_email(self):
    #     rv = self.app.post('/graph_summary', data=dict(
    #         text='843855'), follow_redirects=True)
    #     rv = self.app.post('/email_it', data=dict(
    #         text='testuser3216@gmail.com'), follow_redirects=True)
    #     assert 'Email Sent!' in rv.data

    def test_page_not_found(self):
        rv = self.app.get('/graph_summary/notarounte')
        assert 'What you were looking for is just not there.' in rv.data

    def test_method_not_allowed(self):
        rv = self.app.post('/rcstatmain', data=dict(
            adsfasdf='askdjfhaf'), follow_redirects=True)
        assert 'Method Not Allowed' in rv.data

    def test_bad_request(self):
        rv = self.app.post('/graph_summary', data=dict(
            adsfasdf='askdjfhaf'), follow_redirects=True)
        assert 'Try again?' in rv.data
        assert 'Bad Request' in rv.data

    def test_invalid_usernames(self):
        rv = self.app.post('/table_previous_jobids', data=dict(
            username=''), follow_redirects=True)
        assert 'Username not found' in rv.data
        rv = self.app.post('/table_previous_jobids', data=dict(
            username='asdaffaafff!234'), follow_redirects=True)
        assert 'Username not found' in rv.data

if __name__ == '__main__':
    unittest.main()
