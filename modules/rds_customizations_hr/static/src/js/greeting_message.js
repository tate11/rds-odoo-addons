odoo.define('rds_customizations_hr.greeting_message', function (require) {
"use strict";

var core = require('web.core');

var _t = core._t;

var GreetingMessage = require('hr_attendance.greeting_message');

GreetingMessage.include({


    farewell_message: function() {
        var self = this;
        var now = this.attendance.check_out.clone();
        this.return_to_main_menu = setTimeout( function() { self.do_action(self.next_action, {clear_breadcrumbs: true}); }, 5000);

        if(this.previous_attendance_change_date){
            var last_check_in_date = this.previous_attendance_change_date.clone();
            if(now - last_check_in_date > 1000*60*60*12){
                this.$('.o_hr_attendance_warning_message').show().append(_t("<b>Warning! Last check in was over 12 hours ago.</b><br/>If this isn't right, please contact Human Resource staff"));
                //clearTimeout(this.return_to_main_menu);
                //this.activeBarcode = false;
            } else if(now - last_check_in_date > 1000*60*60*8){
                this.$('.o_hr_attendance_random_message').html(_t("Another good day's work! See you soon!"));
            }
        }

        if (now.hours() < 12) {
            this.$('.o_hr_attendance_message_message').append(_t("Have a good day!"));
        } else if (now.hours() < 14) {
            this.$('.o_hr_attendance_message_message').append(_t("Have a nice lunch!"));
            if (Math.random() < 0.05) {
                this.$('.o_hr_attendance_random_message').html(_t("Eat breakfast as a king, lunch as a merchant and supper as a beggar"));
            } else if (Math.random() < 0.06) {
                this.$('.o_hr_attendance_random_message').html(_t("An apple a day keeps the doctor away"));
            }
        } else if (now.hours() < 17) {
            this.$('.o_hr_attendance_message_message').append(_t("Have a good afternoon"));
        } else {
            if (now.hours() < 18 && Math.random() < 0.2) {
                this.$('.o_hr_attendance_message_message').append(_t("Early to bed and early to rise, makes a man healthy, wealthy and wise"));
            } else {
                this.$('.o_hr_attendance_message_message').append(_t("Have a good evening"));
            }
        }
    },
});

//core.action_registry.add('hr_attendance_greeting_message', GreetingMessage);

//return GreetingMessage;

});
