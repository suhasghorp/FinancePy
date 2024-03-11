##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################


from ...utils.error import FinError
from ...utils.date import Date
from ...utils.calendar import Calendar
from ...utils.calendar import CalendarTypes
from ...utils.calendar import BusDayAdjustTypes
from ...utils.day_count import DayCount, DayCountTypes
from ...utils.helpers import label_to_string, check_argument_types
from ...market.curves.discount_curve import DiscountCurve

###############################################################################


class IborFRA:
    """ Class for managing LIBOR forward rate agreements. A forward rate
    agreement is an agreement to exchange a fixed pre-agreed rate for a
    floating rate linked to LIBOR that is not known until some specified
    future fixing date. The FRA payment occurs on or soon after this date
    on the FRA settlement date. Typically the timing gap is two days.

    A FRA is used to hedge a Ibor quality loan or lend of some agreed
    notional amount. This period starts on the settlement date of the
    FRA and ends on the maturity date of the FRA. For example a 1x4 FRA
    relates to a Ibor starting in 1 month for a loan period ending in 4
    months. Hence it links to 3-month Ibor rate. The amount received by a
    payer of fixed rate at settlement is:

        acc(1,2) * (Ibor(1,2) - FRA RATE) / (1 + acc(0,1) x Ibor(0,1))

    So the value at time 0 is

        acc(1,2) * (FWD Ibor(1,2) - FRA RATE) x df(0,2)

    If the base date of the curve is before the value date then we
    forward adjust this amount to that value date. For simplicity I have
    assumed that the fixing date and the settlement date are the same date.
    This should be amended later.

    The valuation below incorporates a dual curve approach.
    """

    def __init__(self,
                 start_dt: Date,  # The date the FRA starts to accrue
                 # End of the Ibor rate period
                 maturity_dt_or_tenor: (Date, str),
                 fra_rate: float,  # The fixed contractual FRA rate
                 dc_type: DayCountTypes,  # For interest period
                 notional: float = 100.0,
                 pay_fixed_rate: bool = True,  # True if the FRA rate is being paid
                 cal_type: CalendarTypes = CalendarTypes.WEEKEND,
                 bd_type: BusDayAdjustTypes = BusDayAdjustTypes.MODIFIED_FOLLOWING):
        """ Create a Forward Rate Agreement object. """

        check_argument_types(self.__init__, locals())

        self.cal_type = cal_type
        self.bd_type = bd_type

        if isinstance(maturity_dt_or_tenor, Date):
            maturity_dt = maturity_dt_or_tenor
        else:
            maturity_dt = start_dt.add_tenor(maturity_dt_or_tenor)
            calendar = Calendar(self.cal_type)
            maturity_dt = calendar.adjust(maturity_dt,
                                            self.bd_type)

        if start_dt > maturity_dt:
            raise FinError("Settlement date after maturity date")

        self.start_dt = start_dt
        self.maturity_dt = maturity_dt
        self.fra_rate = fra_rate
        self.pay_fixed_rate = pay_fixed_rate
        self.dc_type = dc_type
        self.notional = notional

    ###########################################################################

    def value(self,
              value_dt: Date,
              discount_curve: DiscountCurve,
              index_curve: DiscountCurve = None):
        """ Determine mark to market value of a FRA contract based on the
        market FRA rate. We allow the pricing to have a different curve for
        the Libor index and the discounting of promised cash flows. """

        if index_curve is None:
            index_curve = discount_curve

        # Get the Libor index from the index curve
        dc = DayCount(self.dc_type)
        acc_factor = dc.year_frac(self.start_dt, self.maturity_dt)[0]
        df_index1 = index_curve.df(self.start_dt)
        df_index2 = index_curve.df(self.maturity_dt)
        libor_fwd = (df_index1 / df_index2 - 1.0) / acc_factor

        # Get the discount factor from a discount curve
        df_mat = discount_curve.df(self.maturity_dt)

        v = acc_factor * (libor_fwd - self.fra_rate) * df_mat

        # Forward value the FRA to the value date
        df_value = discount_curve.df(value_dt)
        v = v * self.notional / df_value

        if self.pay_fixed_rate is True:
            v *= -1.0
        return v

    ##########################################################################

    def maturity_df(self, index_curve):
        """ Determine the maturity date index discount factor needed to refit
        the market FRA rate. In a dual-curve world, this is not the discount
        rate discount factor but the index curve discount factor. """

        dc = DayCount(self.dc_type)
        df1 = index_curve.df(self.start_dt)
        acc_factor = dc.year_frac(self.start_dt, self.maturity_dt)[0]
        df2 = df1 / (1.0 + acc_factor * self.fra_rate)
        return df2

    ###########################################################################

    def print_payments(self, value_dt):
        """ Determine the value of the Deposit given a Ibor curve. """

        flow_settle = self.notional
        dc = DayCount(self.dc_type)
        acc_factor = dc.year_frac(self.start_dt, self.maturity_dt)[0]
        flow_maturity = (1.0 + acc_factor * self.fra_rate) * self.notional

        if self.pay_fixed_rate is True:
            print(self.start_dt, -flow_settle)
            print(self.maturity_dt, flow_maturity)
        else:
            print(self.start_dt, flow_settle)
            print(self.maturity_dt, -flow_maturity)

    ##########################################################################

    def __repr__(self):
        s = label_to_string("OBJECT TYPE", type(self).__name__)
        s += label_to_string("START ACCD DATE", self.start_dt)
        s += label_to_string("MATURITY DATE", self.maturity_dt)
        s += label_to_string("FRA RATE", self.fra_rate)
        s += label_to_string("NOTIONAL", self.notional)
        s += label_to_string("PAY FIXED RATE", self.pay_fixed_rate)
        s += label_to_string("DAY COUNT TYPE", self.dc_type)
        s += label_to_string("BUS DAY ADJUST TYPE", self.bd_type)
        s += label_to_string("CALENDAR", self.cal_type)
        return s

    ###########################################################################

    def _print(self):
        print(self)

###############################################################################
