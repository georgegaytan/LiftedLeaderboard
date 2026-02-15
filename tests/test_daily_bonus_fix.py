from src.models.activity_record import ActivityRecord


class TestDailyBonusFix:
    '''Test that daily bonus triggers correctly after weekly validation changes.'''

    def test_activity_group_key_daily_steps(self):
        '''Test that daily steps get the correct group key.'''
        group_key = ActivityRecord._activity_group_key('Steps', 'Daily Steps 10k+')
        assert group_key == 'steps_daily'

        group_key = ActivityRecord._activity_group_key('Steps', 'Daily Steps 5k+')
        assert group_key == 'steps_daily'

    def test_activity_group_key_weekly_steps(self):
        '''Test that weekly steps get the correct group key.'''
        group_key = ActivityRecord._activity_group_key('Steps', 'Weekly Steps 70k+')
        assert group_key == 'steps_weekly'

        group_key = ActivityRecord._activity_group_key('Steps', 'Weekly Steps 50k+')
        assert group_key == 'steps_weekly'

    def test_activity_group_key_regular_activities(self):
        '''Test that regular activities return None group key.'''
        group_key = ActivityRecord._activity_group_key('Fitness', 'Running')
        assert group_key is None

        group_key = ActivityRecord._activity_group_key('Diet', 'Healthy Meal')
        assert group_key is None

    def test_activity_group_key_weekly_recovery(self):
        '''Test that weekly recovery activities get correct group key.'''
        group_key = ActivityRecord._activity_group_key(
            'Recovery', 'A week of good sleep (7+ hours/day avg)'
        )
        assert group_key == 'recovery_weekly_sleep'

        group_key = ActivityRecord._activity_group_key(
            'Recovery', 'A week of great sleep (8+ hours/day avg)'
        )
        assert group_key == 'recovery_weekly_sleep'

    def test_activity_group_key_weekly_diet(self):
        '''Test that weekly diet activities get correct group key.'''
        group_key = ActivityRecord._activity_group_key('Diet', 'Week of no Alcohol')
        assert group_key == 'diet_weekly_no_alcohol'

    def test_validation_logic_separation(self):
        '''
        Test that the validation logic properly separates daily and weekly activities.
        '''
        # This test verifies that the group keys are distinct
        # and won't interfere with each other in the validation logic

        daily_activities = [
            ('Steps', 'Daily Steps 10k+'),
            ('Steps', 'Daily Steps 5k+'),
        ]

        weekly_activities = [
            ('Steps', 'Weekly Steps 70k+'),
            ('Steps', 'Weekly Steps 50k+'),
            ('Recovery', 'A week of good sleep (7+ hours/day avg)'),
            ('Recovery', 'A week of great sleep (8+ hours/day avg)'),
            ('Diet', 'Week of no Alcohol'),
        ]

        # Verify daily activities get daily keys
        for category, name in daily_activities:
            group_key = ActivityRecord._activity_group_key(category, name)
            assert group_key == 'steps_daily', f'{name} should get steps_daily key'

        # Verify weekly activities get weekly keys
        weekly_keys = set()
        for category, name in weekly_activities:
            group_key = ActivityRecord._activity_group_key(category, name)
            assert group_key is not None, f'{name} should get a group key'
            assert group_key != 'steps_daily', f'{name} should not get steps_daily key'
            weekly_keys.add(group_key)

        # Verify we have the expected weekly keys
        expected_weekly_keys = {
            'steps_weekly',
            'recovery_weekly_sleep',
            'diet_weekly_no_alcohol',
        }
        assert (
            weekly_keys == expected_weekly_keys
        ), f'Expected {expected_weekly_keys}, got {weekly_keys}'
