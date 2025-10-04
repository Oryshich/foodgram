from rest_framework.exceptions import ValidationError


class PreventSelfSubscribeValidator:

    def __init__(self, fields):
        self.fields = fields

    def __call__(self, attrs):
        user = attrs.get('user')
        following = attrs.get('following')

        if user == following:
            raise ValidationError('Нельзя подписываться на самого себя')
