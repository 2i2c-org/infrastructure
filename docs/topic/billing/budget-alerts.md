(topic:billing:budget-alerts)=
# Cloud Billing Budget Alerts

"I forgot to turn off my cloud resources, your honor" as a reason for declaring
bankruptcy is second only to "The US healthcare system sucks, your honor" in the
US court system. "How much is my cloud going to cost?" is a big anxiety for a lot
of our users, and hence us. We set up billing alerts to help deal with this anxiety.

See [](howto:enable-budget-alerts) for instructions on enabling this feature.

## When are the alerts triggered?

Budget alerts are sent under two conditions:

1. When *forecasted monthly spend* at end of the month goes over our spending limit.
   This is an *early warning* system, that helps us evaluate where spend is going
   and make sure this is expected.
2. When *current actual spend* goves over 100% of our spending limit.

## What to do when we receive an alert?

The current goal is to just make sure we don't end up spending *wildly* more money
than budgeted. So if the forecasted spend busts through on day 5 of the month,
we might need to do something different than if it does on day 30. If it is expected
to overshoot by 500% vs by 10$, our actions might be different. One valid action is
we just adjust the forecast. As an organization, we need more experience with costs
to figure out what the right thing to do is. So our current primary goal would
be to work with our stakeholders and gather that experience.

## Where are these alerts sent?

Budget alerts are "Cliff Alerts" - they don't indicate a current outage (unlike
uptime checks), but indicate that we are perhaps heading in a direction that will
cause problems soon if we do not course correct. Hence, we do not send them to
PagerDuty but to our `support@2i2c.org` email address.
