import json
import os
import hmac
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
STUB=r'''
use utf8;use JSON::PP;
our(%in,$session_id,$remote_user,$writes);$writes=0;$session_id='ui-test-session';$remote_user='root';
sub ftps_load_virtualmin {delete $ENV{'REQUEST_METHOD'};}
sub virtual_server::master_admin {return 1;}
require '__HELPER__';
*main::ftps_rotation_backend=sub {
    my($request)=@_;
    if ($request->{operation} ne 'read') {$writes++ if $request->{operation} eq 'save';return {saved=>$request->{operation} eq 'save'?1:0};}
    return {rotation=>{},domains=>{'1'=>{domain=>'one.example<script>'}},revision=>'revision',installed=>1};
};
sub ReadParse {%in=%{decode_json(do {local $/;<STDIN>})};}
sub html_escape {my($s)=@_;$s='' if !defined($s);$s=~s/&/&amp;/g;$s=~s/</&lt;/g;$s=~s/>/&gt;/g;$s=~s/"/&quot;/g;return $s;}
sub ui_print_header {print "Content-Type: text/html; charset=UTF-8\n\n";}
sub ui_print_footer {print '<footer data-writes="'.$writes.'">Webmin</footer>';}
sub ui_form_start {return '<form action="'.$_[0].'" method="'.$_[1].'">';}
sub ui_form_end {my($bs)=@_;return join('',map {'<button name="'.$_->[0].'">'.$_->[1].'</button>'} @{$bs||[]}).'</form>';}
sub ui_select {my($n,$v,$choices)=@_;return '<select name="'.$n.'">'.join('',map {'<option value="'.html_escape($_->[0]).'"'.($_->[0] eq $v?' selected':'').'>'.html_escape($_->[1]).'</option>'} @$choices).'</select>';}
sub ui_submit {return '<input type="submit" name="'.html_escape($_[1]).'" value="'.html_escape($_[0]).'">';}
sub ui_hidden {return '<input type="hidden" name="'.$_[0].'" value="'.html_escape($_[1]).'">';}
sub ui_table_start {return '<table>';}
sub ui_table_end {return '</table>';}
sub ui_table_row {return '<tr><th>'.$_[0].'</th><td>'.$_[1].'</td></tr>';}
sub ui_checkbox {return '<input type="checkbox" name="'.$_[0].'" value="'.$_[1].'"'.($_[3]?' checked':'').'>'.$_[2];}
sub ui_textbox {return '<input name="'.$_[0].'" value="'.html_escape($_[1]).'">';}
1;
'''
class RotationPage(unittest.TestCase):
    def page(self,method='GET',**data):
        with tempfile.TemporaryDirectory() as tmp:
            helper=str(ROOT/'virtualmin-ftps/rotation-ui-lib.pl')
            Path(tmp,'virtualmin-ftps-lib.pl').write_text(STUB.replace('__HELPER__',helper))
            Path(tmp,'rotation.cgi').write_bytes((ROOT/'virtualmin-ftps/rotation.cgi').read_bytes())
            p=subprocess.run(['perl','rotation.cgi'],cwd=tmp,input=json.dumps(data).encode(),capture_output=True,env=dict(os.environ,REQUEST_METHOD=method))
        self.assertEqual(p.returncode,0,p.stderr.decode());return p.stdout.decode('utf-8')
    def test_global_form_and_utf8(self):
        html=self.page()
        for s in ('Wöchentlich','Täglich','Größenrotation','name="preview"','name="save"','value="52"'):
            self.assertIn(s,html)
        self.assertNotIn('�',html);self.assertNotIn('WÃ¶',html)
    def test_domain_form_has_inheritance_and_escaped_name(self):
        html=self.page(dom='1')
        self.assertIn('name="inherit"',html);self.assertIn('one.example&lt;script&gt;',html)
        self.assertNotIn('one.example<script>',html)

    def submit(self, method='POST', **changes):
        token=hmac.new(b'ui-test-session\0root',b'virtualmin-ftps/logrotation',hashlib.sha256).hexdigest()
        data=dict(save='Speichern',interval='weekly',rotate='52',maxsize='',revision='revision',token=token)
        data.update(changes)
        return self.page(method=method,**data)
    def test_save_survives_environment_cleanup(self):
        html=self.submit()
        self.assertIn('Einstellungen gespeichert',html)
        self.assertIn('data-writes="1"',html)
        self.assertNotIn('erfordert ein Formular mit POST',html)
    def test_preview_survives_environment_cleanup_without_saving(self):
        html=self.submit(save='',preview='Prüfen')
        self.assertIn('Einstellungen sind gültig',html)
        self.assertIn('data-writes="0"',html)
    def test_get_save_still_denied_after_cleanup(self):
        html=self.submit(method='GET')
        self.assertIn('erfordert ein Formular mit POST',html)
        self.assertIn('data-writes="0"',html)
    def test_post_with_invalid_token_still_denied(self):
        html=self.submit(token='invalid')
        self.assertIn('Ungültiges Formular',html)
        self.assertIn('data-writes="0"',html)
        self.assertIn('name="save"',html)

    def test_single_post_form_for_authentic_ajax_method_detection(self):
        class Forms(HTMLParser):
            def __init__(self):super().__init__();self.forms=[];self.active=None
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs)
                if tag=='form':
                    assert self.active is None, 'nested forms'
                    self.active={'attributes':attrs,'fields':[]};self.forms.append(self.active)
                elif self.active is not None and tag in ('input','button','select'):
                    self.active['fields'].append(attrs.get('name'))
            def handle_endtag(self,tag):
                if tag=='form':self.active=None
        parser=Forms();parser.feed(self.page())
        self.assertEqual(len(parser.forms),1)
        form=parser.forms[0]
        self.assertEqual(form['attributes'].get('action'),'rotation.cgi')
        self.assertEqual(form['attributes'].get('method'),'post')
        self.assertTrue({'host','show','dom','token','revision','rotate','preview','save'} <= set(form['fields']))
        # Authentic get_pjax_type(string URL) uses the first matching form's
        # method. Exercise that transport selection, not a hard-coded POST.
        html=self.submit(method=form['attributes']['method'].upper())
        self.assertIn('data-writes="1"',html)

    def test_show_selects_host_without_writing(self):
        html=self.submit(show='Anzeigen',host='1',dom='')
        self.assertIn('Zeitplan für one.example&lt;script&gt;',html)
        self.assertIn('name="dom" value="1"',html)
        self.assertIn('data-writes="0"',html)

    def test_selector_change_alone_does_not_retarget_save(self):
        html=self.submit(host='1',dom='')
        self.assertIn('Gemeinsamer Zeitplan',html)
        self.assertNotIn('Zeitplan für one.example',html)
        self.assertIn('name="dom" value=""',html)
        self.assertIn('data-writes="1"',html)
