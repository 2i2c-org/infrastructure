---
name: "\U0001F4C5 Event for a community"
about: Coordination and planning around an event for a community
title: "[EVENT] {{ HUB NAME }}"
labels: 'event'
assignees: ''

---

### Summary

<!-- Please provide a short, one-sentence summary about this event. -->

### Info

- **Event begin:** <!-- The date that the event will start. -->
- **Event end:** <!-- The date that the event will end. -->
- **Community Representative:** <!-- The GitHub ID of the current representative for the Hub and Community, e.g. @octocat -->
- **Hub URL**: <!-- The URL of the hub that will be used for the event -->
- **Hub decommisioned after event?**: <!-- Will this hub be decommissioned after the event is over? -->

### Task List

**Before the event**

- [ ] Dates confirmed with the community representative
- [ ] **One week before event** Hub is running.
- [ ] Confirm with Community Representative that their workflows function as expected.
  - <details>
    <summary>👉Template message to send to community representative</summary>
    
    ```
    Hey {{ COMMUNITY REPRESENTATIVE }}, the date of your event is getting close!
    
    Could you please confirm that your hub environment is ready-to-go, and matches your hub's infrastructure setup, by ensuring the following things:
    - [ ] Log-in and authentication works as-expected
    - [ ] `nbgitpuller` links you intend to use resolve properly
    - [ ] Your notebooks run as-expected
    
    </details>  

- [ ] **1 day before event** A separate nodegroup is provisioned for the event

**During and after event**

- [ ] Confirm event is finished.
- [ ] Nodegroup created for the hub is decommissioned.
- [ ] Hub decommissioned (if needed).
- [ ] Debrief with community representative.
  - <details>
    <summary>👉Template debrief to send to community representative</summary>
      
     ```
     Hey {{ COMMUNITY REPRESENTATIVE }}, your event appears to be over 🎉
     
     We hope that your hub worked out well for you! We are trying to understand where we can improve our hub infrastructure and setup around events, and would love any feedback that you're willing to give. Would you mind answering the following questions? If not, just let us know and that is no problem!
  
     - Did the infrastructure behave as expected?
     - Anything that was confusing or could be improved?
     - Any extra functionality you wish you would have had?
     - Could you share a story about how you used the hub?

     - Any other feedback that you'd like to share?
     
     ```

    </details>  
