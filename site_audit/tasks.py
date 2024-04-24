import django
import modal
from modal import Image

site_audit = modal.App("site_audit")
django_app_image = (
    Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
    .workdir("/app")
    .env({"DJANGO_SETTINGS_MODULE": "noname.settings"})
    .copy_local_dir("bin", "/app/bin")
    .copy_local_dir("commons", "/app/commons")
    .copy_local_dir("contacts", "/app/contacts")
    .copy_local_dir("users", "/app/users")
    .copy_local_dir("theme", "/app/theme")
    .copy_local_dir("noname", "/app/noname")
    .copy_local_dir("site_audit", "/app/site_audit")
    .copy_local_file("manage.py", "/app/manage.py")
)
playwright_image = (
    Image.debian_slim(python_version="3.11")
    .pip_install("playwright==1.42.0")
    .run_commands("playwright install")
)


@site_audit.function(image=playwright_image)
def visit_page(x):
    pass

@site_audit.function(image=django_app_image, secrets=[modal.Secret.from_name("database")])
def test_crawl(x):
    django.setup()
    from commons.utils import OpenAndCloseDbConnection
    from users.models import Account
    from site_audit.crawlers import Crawler

    with OpenAndCloseDbConnection():
        print(Account.objects.count())

    crawler = Crawler("https://www.neurelo.com/")
    crawler.crawl()
    return x**2


@site_audit.function()
def daily_crawl(image=django_app_image, schedule=modal.Cron("0 8 * * 1")):
    print("This code is running on a remote worker!")
    return
