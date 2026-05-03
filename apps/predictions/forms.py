"""apps/predictions/forms.py"""
from django import forms

CATEGORY_CHOICES = [
    ('',       'Select category'),
    ('GEN',    'General (GEN)'),
    ('OBC',    'OBC'),
    ('SC',     'SC'),
    ('ST',     'ST'),
    ('EWS',    'EWS'),
    ('GEN-PH', 'GEN – PwBD'),
    ('OBC-PH', 'OBC – PwBD'),
    ('SC-PH',  'SC – PwBD'),
    ('ST-PH',  'ST – PwBD'),
]

QUOTA_CHOICES = [
    ('',    'All Quotas'),
    ('AIQ', 'All India Quota (15%)'),
    ('SQ',  'State Quota (85%)'),
    ('MQ',  'Management Quota'),
]

COURSE_CHOICES = [
    ('MBBS', 'MBBS (Medical)'),
    ('BDS',  'BDS (Dental)'),
    ('BAMS', 'BAMS (Ayurveda)'),
    ('BHMS', 'BHMS (Homeopathy)'),
    ('BUMS', 'BUMS (Unani)'),
]

STATE_CHOICES = [
    ('', 'All States (pan-India)'),
    ('Andhra Pradesh','Andhra Pradesh'),('Assam','Assam'),('Bihar','Bihar'),
    ('Chandigarh','Chandigarh'),
    ('Chhattisgarh','Chhattisgarh'),('Delhi','Delhi'),('Goa','Goa'),
    ('Gujarat','Gujarat'),('Haryana','Haryana'),('Himachal Pradesh','Himachal Pradesh'),
    ('Jammu And Kashmir','Jammu & Kashmir'),('Jharkhand','Jharkhand'),
    ('Karnataka','Karnataka'),('Kerala','Kerala'),('Madhya Pradesh','Madhya Pradesh'),
    ('Maharashtra','Maharashtra'),('Manipur','Manipur'),('Meghalaya','Meghalaya'),
    ('Nagaland','Nagaland'),('Odisha','Odisha'),('Puducherry','Puducherry'),
    ('Punjab','Punjab'),('Rajasthan','Rajasthan'),('Tamil Nadu','Tamil Nadu'),
    ('Telangana','Telangana'),('Tripura','Tripura'),('Uttar Pradesh','Uttar Pradesh'),
    ('Uttarakhand','Uttarakhand'),('West Bengal','West Bengal'),
]

SORT_CHOICES = [
    ('score',        'Best Score First'),
    ('tier',         'Tier (Safe → Target → Dream)'),
    ('closing_rank', 'Closing Rank'),
]

COLLEGE_TYPE_CHOICES = [
    ('',        'All Types'),
    ('GOVT',    'Government'),
    ('CENTRAL', 'Central (AIIMS/JIPMER)'),
    ('PRIVATE', 'Private'),
    ('DEEMED',  'Deemed University'),
]

INPUT_MODE_CHOICES = [
    ('rank',  'NEET Rank'),
    ('score', 'NEET Score'),
]

_cls = lambda c: {'class': c}

class PredictionForm(forms.Form):
    input_mode = forms.ChoiceField(
        label='Input Mode', choices=INPUT_MODE_CHOICES, initial='rank',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=False,
    )
    rank = forms.IntegerField(
        label='NEET All India Rank', min_value=1, max_value=2_000_000,
        required=False,
        widget=forms.NumberInput(attrs={'class':'form-control form-control-lg',
                                        'placeholder':'e.g. 45000', 'autofocus': True}),
        error_messages={'min_value':'Rank must be ≥ 1.',
                        'invalid':'Enter a whole number.'},
    )
    neet_score = forms.IntegerField(
        label='NEET Score (out of 720)', min_value=0, max_value=720,
        required=False,
        widget=forms.NumberInput(attrs={'class':'form-control form-control-lg',
                                        'placeholder':'e.g. 550'}),
        error_messages={'min_value':'Score must be ≥ 0.',
                        'max_value':'Score must be ≤ 720.',
                        'invalid':'Enter a whole number.'},
    )
    category = forms.ChoiceField(
        label='Category', choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class':'form-select form-select-lg'}),
    )
    state = forms.ChoiceField(
        label='Home State', choices=STATE_CHOICES, required=False,
        widget=forms.Select(attrs={'class':'form-select form-select-lg'}),
    )
    quota = forms.ChoiceField(
        label='Quota', choices=QUOTA_CHOICES, required=False,
        widget=forms.Select(attrs={'class':'form-select form-select-lg'}),
    )
    college_type = forms.ChoiceField(
        label='College Type', choices=COLLEGE_TYPE_CHOICES, required=False,
        widget=forms.Select(attrs={'class':'form-select form-select-lg'}),
    )
    sort_by = forms.ChoiceField(
        label='Sort By', choices=SORT_CHOICES, initial='score',
        widget=forms.Select(attrs={'class':'form-select form-select-lg'}),
    )
    budget = forms.IntegerField(
        label='Max Annual Fee Budget (₹)', min_value=0, required=False,
        widget=forms.NumberInput(attrs={'class':'form-control form-control-lg',
                                        'placeholder':'e.g. 500000 (optional)'}),
    )
    course = forms.ChoiceField(
        label='Course', choices=COURSE_CHOICES, initial='MBBS',
        widget=forms.Select(attrs={'class':'form-select form-select-lg'}),
    )

    def clean(self):
        data = super().clean()
        rank = data.get('rank')
        score = data.get('neet_score')
        mode = data.get('input_mode', 'rank')

        if mode == 'score' and score is not None:
            # Convert score to rank
            from ml.ml_model import score_to_rank
            data['rank'] = score_to_rank(score)
        elif rank is None:
            raise forms.ValidationError('Please enter either your NEET Rank or NEET Score.')
        return data

    def clean_category(self):
        v = self.cleaned_data.get('category', '')
        if not v:
            raise forms.ValidationError('Please select your category.')
        return v.upper()

    def clean_state(self):
        return self.cleaned_data.get('state', '').strip() or None

    def clean_quota(self):
        v = self.cleaned_data.get('quota', '').strip()
        return v.upper() if v else None

    def clean_college_type(self):
        v = self.cleaned_data.get('college_type', '').strip()
        return v.upper() if v else None

    def clean_sort_by(self):
        return self.cleaned_data.get('sort_by') or 'score'

    def to_pipeline_kwargs(self) -> dict:
        return {
            'rank'         : self.cleaned_data['rank'],
            'category'     : self.cleaned_data['category'],
            'state'        : self.cleaned_data['state'],
            'quota'        : self.cleaned_data['quota'],
            'college_type' : self.cleaned_data['college_type'],
            'sort_by'      : self.cleaned_data['sort_by'],
            'course'       : self.cleaned_data['course'],
        }
