import json
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
STUB=r'''
use utf8;use JSON::PP;
our(%in,$session_id,$remote_user);$session_id='ui-test-session';$remote_user='root';
sub ftps_load_virtualmin {}
sub virtual_server::master_admin {return 1;}
require '__HELPER__';
*main::ftps_rotation_backend=sub {
    my($request)=@_;
    return {saved=>$request->{operation} eq 'save'?1:0} if $request->{operation} ne 'read';
    return {rotation=>{},domains=>{'1'=>{domain=>'one.example<script>'}},revision=>'revision',installed=>1};
};
sub ReadParse {%in=%{decode_json(do {local $/;<STDIN>})};}
sub html_escape {my($s)=@_;$s='' if !defined($s);$s=~s/&/&amp;/g;$s=~s/</&lt;/g;$s=~s/>/&gt;/g;$s=~s/"/&quot;/g;return $s;}
sub ui_print_header {print "Content-Type: text/html; charset=UTF-8\n\n";}
sub ui_print_footer {print '<footer>Webmin</footer>';}
sub ui_form_start {return '<form action="'.$_[0].'" method="'.$_[1].'">';}
sub ui_form_end {my($bs)=@_;return join('',map {'<button name="'.$_->[0].'">'.$_->[1].'</button>'} @{$bs||[]}).'</form>';}
sub ui_select {my($n,$v,$choices)=@_;return '<select name="'.$n.'">'.join('',map {'<option value="'.html_escape($_->[0]).'"'.($_->[0] eq $v?' selected':'').'>'.html_escape($_->[1]).'</option>'} @$choices).'</select>';}
sub ui_submit {return '<input type="submit" value="'.html_escape($_[0]).'">';}
sub ui_hidden {return '<input type="hidden" name="'.$_[0].'" value="'.html_escape($_[1]).'">';}
sub ui_table_start {return '<table>';}
sub ui_table_end {return '</table>';}
sub ui_table_row {return '<tr><th>'.$_[0].'</th><td>'.$_[1].'</td></tr>';}
sub ui_checkbox {return '<input type="checkbox" name="'.$_[0].'" value="'.$_[1].'"'.($_[3]?' checked':'').'>'.$_[2];}
sub ui_textbox {return '<input name="'.$_[0].'" value="'.html_escape($_[1]).'">';}
1;
'''
class RotationPage(unittest.TestCase):
    def page(self,**data):
        with tempfile.TemporaryDirectory() as tmp:
            helper=str(ROOT/'virtualmin-ftps/rotation-ui-lib.pl')
            Path(tmp,'virtualmin-ftps-lib.pl').write_text(STUB.replace('__HELPER__',helper))
            Path(tmp,'rotation.cgi').write_bytes((ROOT/'virtualmin-ftps/rotation.cgi').read_bytes())
            p=subprocess.run(['perl','rotation.cgi'],cwd=tmp,input=json.dumps(data).encode(),capture_output=True)
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
