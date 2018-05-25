#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

group = "checkparams"


register_check_parameters(
   subgroup_environment,
    "apc_smart",
    _("APC SMART Checks"),
    Transform(
        Dictionary(
            elements = [
                ("levels",
                Tuple(
                    title = _("Levels of battery parameters during normal operation"),
                    elements = [
                        Integer(
                            title = _("Critical Battery Capacity"),
                            help = _("The battery capacity in percent at and below which a critical state is triggered"),
                            unit = "%", default_value = 95,
                        ),
                        Integer(
                            title = _("Critical System Temperature"),
                            help = _("The critical temperature of the System"),
                            unit = _("C"),
                            default_value = 55,
                        ),
                        Integer(
                            title = _("Critical Battery Current"),
                            help = _("The critical battery current in Ampere"),
                            unit = _("A"),
                            default_value = 1000000,
                        ),
                        Integer(
                            title = _("Critical Battery Voltage"),
                            help = _("The output voltage at and below which a critical state "
                                     "is triggered."),
                            unit = _("V"),
                            default_value = 220,
                        ),
                    ]
                )),
                ("output_load",
                Tuple(
                  title = _("Current Output Load"),
                  help = _("Here you can set levels on the current percentual output load of the UPS. "
                           "This load affects the running time of all components being supplied "
                           "with battery power."),
                  elements = [
                     Percentage(
                         title = _("Warning level"),
                     ),
                     Percentage(
                         title = _("Critical level"),
                     ),
                  ]
                )),
                ("post_calibration_levels",
                Dictionary(
                    title = _("Levels of battery parameters after calibration"),
                    help = _("After a battery calibration the battery capacity is reduced until the "
                             "battery is fully charged again. Here you can specify an alternative "
                             "lower level in this post-calibration phase. "
                             "Since apc devices remember the time of the last calibration only "
                             "as a date, the alternative lower level will be applied on the whole "
                             "day of the calibration until midnight. You can extend this time period "
                             "with an additional time span to make sure calibrations occuring just "
                             "before midnight do not trigger false alarms."
                    ),
                    elements = [
                        ("altcapacity",
                        Percentage(
                            title = _("Alternative critical battery capacity after calibration"),
                            default_value = 50,
                        )),
                        ("additional_time_span",
                        Integer(
                            title = ("Extend post-calibration phase by additional time span"),
                            unit = _("minutes"),
                            default_value = 0,
                        )),
                    ],
                    optional_keys = False,
                )),
            ],
            optional_keys = ['post_calibration_levels', 'output_load'],
        ),
        forth = apc_convert_from_tuple
    ),
    None,
    "first"
)

