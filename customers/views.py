from django.shortcuts import get_object_or_404
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from accounts.forms import UserInfoForm, UserProfileForm
from accounts.models import UserProfile


class CProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'customers/cprofile.html'
    success_url = reverse_lazy('cprofile')

    def get_object(self):
        # Get the UserProfile for the logged-in user
        return get_object_or_404(UserProfile, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = UserInfoForm(instance=self.request.user)
        return context

    def form_valid(self, form):
        user_form = UserInfoForm(self.request.POST, instance=self.request.user)
        if user_form.is_valid():
            user_form.save()
            messages.success(self.request, 'Profile updated successfully!')
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        context['user_form'] = UserInfoForm(instance=self.request.user)
        return self.render_to_response(context)
