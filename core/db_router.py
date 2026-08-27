class DualDatabaseRouter:
    """
    Routes specific Django apps to Supabase and all other apps to Render/Default.
    """
    # Define which Django apps should be routed to Supabase
    SUPABASE_APPS = {'jobs'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.SUPABASE_APPS:
            return 'supabase'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.SUPABASE_APPS:
            return 'supabase'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations if both objects belong to the same app/database
        db_obj1 = 'supabase' if obj1._meta.app_label in self.SUPABASE_APPS else 'default'
        db_obj2 = 'supabase' if obj2._meta.app_label in self.SUPABASE_APPS else 'default'
        if db_obj1 == db_obj2:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.SUPABASE_APPS:
            return db == 'supabase'
        return db == 'default'