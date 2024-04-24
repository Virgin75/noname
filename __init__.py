import os

if os.environ.get('ASYNC_TASK') == 'MODAL.COM':
    from modal import App
    from site_audit.tasks import site_audit
    from users.tasks import users
    import modal

    app = modal.App("noname")
    app.include(site_audit)
    app.include(users)
