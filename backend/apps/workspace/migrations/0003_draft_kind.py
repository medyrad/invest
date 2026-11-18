from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('workspace','0002_receiveattempt')]
    operations = [migrations.AddField(model_name='draft',name='kind',field=models.CharField(max_length=12,default='project',choices=[('project','project'),('fund','fund'),('sale','sale')]))]
