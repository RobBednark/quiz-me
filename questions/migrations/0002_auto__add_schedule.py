# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Schedule'
        db.create_table(u'questions_schedule', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('date_show_next', self.gf('django.db.models.fields.DateTimeField')()),
            ('interval_num', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2)),
            ('interval_unit', self.gf('django.db.models.fields.TextField')()),
            ('interval_secs', self.gf('django.db.models.fields.IntegerField')()),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['questions.Question'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emailusername.User'])),
        ))
        db.send_create_signal(u'questions', ['Schedule'])


    def backwards(self, orm):
        # Deleting model 'Schedule'
        db.delete_table(u'questions_schedule')


    models = {
        u'emailusername.user': {
            'Meta': {'object_name': 'User'},
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'questions.answer': {
            'Meta': {'object_name': 'Answer'},
            'answer': ('django.db.models.fields.TextField', [], {}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.attempt': {
            'Meta': {'object_name': 'Attempt'},
            'attempt': ('django.db.models.fields.TextField', [], {}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.hint': {
            'Meta': {'object_name': 'Hint'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Answer']", 'null': 'True'}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'hint': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.question': {
            'Meta': {'object_name': 'Question'},
            'answer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Answer']", 'null': 'True', 'blank': 'True'}),
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.questiontag': {
            'Meta': {'object_name': 'QuestionTag'},
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Question']"}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.quiz': {
            'Meta': {'object_name': 'Quiz'},
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'})
        },
        u'questions.schedule': {
            'Meta': {'object_name': 'Schedule'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_show_next': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval_num': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'}),
            'interval_secs': ('django.db.models.fields.IntegerField', [], {}),
            'interval_unit': ('django.db.models.fields.TextField', [], {}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']"})
        },
        u'questions.tag': {
            'Meta': {'object_name': 'Tag'},
            'datetime_added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'datetime_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'questions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['questions.Question']", 'null': 'True', 'through': u"orm['questions.QuestionTag']", 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']", 'null': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users'", 'to': u"orm['emailusername.User']", 'through': u"orm['questions.UserTag']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True'})
        },
        u'questions.usertag': {
            'Meta': {'object_name': 'UserTag'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['questions.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['emailusername.User']"})
        }
    }

    complete_apps = ['questions']