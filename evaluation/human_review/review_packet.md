# Draft review packet (50 drafts)

Judge each draft on its own, from the ticket and the retrieved passages shown. Do not discuss
scores with the other assessor until both sheets are finished.

## Rubric

- **hallucination** (`Y` or `N`): `Y` if the draft contains at least one claim that the retrieved
  passages do not support. This includes a fact about the customer's account or situation that
  the ticket does not state, and a feature or step presented as available to a customer whose plan
  (shown below) the passage excludes. Greetings, offers to help and hedged next steps are not claims.
- **citations_total**: the number of `[DOC-...]` citations in the draft (count each occurrence).
- **citations_unsupported**: how many of those citations are attached to a sentence that the cited
  passage does not support. A citation to the right document that does not back its sentence counts.
- **notes**: anything a second reader should know (optional).

Record scores in your own sheet (`assessor_A.csv` or `assessor_B.csv`), one row per ticket.

## 1. VAL-0065

**Channel:** email | **Customer plan:** standard

**Subject:** Billing period dates unclear

**Ticket body:**

> There are charges on our invoice for a service I do not believe we use. Could you explain what these relate to?

**Draft reply:**

> Hi there,
> 
> I can help clarify those charges. According to our documentation, charges for services you do not actively use can often be caused by resources left running in non-production environments (such as staging or development), which are billed at the same rate as production [DOC-BILL-001]. Additionally, usage-based charges may have accrued beyond your plan allowance [DOC-BILL-001].
> 
> To identify exactly what these charges relate to, please follow these steps:
> 1. Open the usage breakdown for the billing period, which itemises charges by service and by environment [DOC-BILL-001].
> 2. Look specifically for resources in staging or development environments [DOC-BILL-001].
> 3. Check the billing period dates at the top of the invoice, as the period runs from the anniversary of your subscription date rather than the first of the month [DOC-BILL-001].
> 
> If you find unexpected accruals, you can set a usage alert on the billing page to be notified during the period rather than at the end [DOC-BILL-001].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-BILL-003**, Usage limits, overage and spend controls: ## Resolution

1. Check the current period usage against the plan allowance on the billing page.
2. Decide deliberately between a hard spend cap, which stops the service, and overage, which continues at the listed rate. Production workloads generally need the second.
3. Configure alerts at fifty, eighty and ninety-five per cent of allowance rather than relying on the cap as a warning.
4. Where a cap has stopped a production service, an account owner can raise it immediately from the billing page and service resumes within a minute.

## Notes

Spend caps apply per organisation and cannot currently be set per project.

---

## 2. VAL-0045

**Channel:** email | **Customer plan:** standard

**Subject:** Export missing recent records

**Ticket body:**

> I started an export over the weekend and it is still showing as queued. It covers about two million records. Should I cancel and try again?

**Draft reply:**

> Hi,
> 
> Based on the documentation, you do not need to cancel the export. Large exports covering more than a million records are processed asynchronously and commonly take several minutes to complete [DOC-DATA-001]. Since your export covers approximately two million records, it is expected to remain in the queue or processing state for a period of time.
> 
> Please check the exports page for the current job status. If the job has completed but the download link has expired, you can request a fresh link from the same page, as the underlying file is retained for seven days [DOC-DATA-001]. Note that the export reflects the data snapshot taken at the moment the job began, so any records created during the processing time will not be included [DOC-DATA-001].
> 
> If you require frequent large exports, consider configuring a scheduled export delivered to object storage [DOC-DATA-001].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-DATA-001 (cited)**, Exporting account data and scheduled extracts: ## Resolution

1. Check the exports page for job status. Jobs covering more than a million records commonly take several minutes.
2. Request a fresh link from the exports page if the original has expired. The underlying file is retained for seven days.
3. Note that the export reflects the moment the job began, so records created during processing are not included.
4. For recurring needs, configure a scheduled export delivered to object storage rather than generating them manually.

## Notes

Exports containing personal data are logged in the audit trail with the requesting user and the fields included.

- **DOC-DATA-001 (cited)**, Exporting account data and scheduled extracts: # Exporting account data and scheduled extracts

**Applies to:** All plans

## Symptoms

- An export has not completed
- The download link has expired
- The export is missing recent records

## Common causes

- Large exports are queued and processed asynchronously
- Download links are valid for twenty-four hours
- The export captured a snapshot taken when the job started

## Resolution

- **DOC-API-002**, Pagination and handling large result sets: ## Resolution

1. Use cursor pagination for anything that may change while you iterate. Offset pagination will skip or repeat records when items are inserted mid-iteration.
2. Pass the next_cursor value from each response as the cursor parameter of the following request, and stop when it is null.
3. Keep page size at or below two hundred. Larger requests are rejected rather than truncated.
4. For very large extracts, use the export endpoint, which runs asynchronously and returns a download link.

## Notes

Cursors expire after one hour. Long-running iterations should handle expiry by restarting from a recorded checkpoint.

- **DOC-SEC-003**, Audit logging and compliance evidence: ## Resolution

1. Filter the audit log by actor, resource and date range. Every administrative action carries the user, the address and the outcome.
2. Export the relevant period to object storage for anything needed beyond the retention window. Exports are not subject to retention limits.
3. Configure continuous export to your own storage if a policy requires retention longer than the plan provides.
4. Note that read access to resources is not logged on Business plans, only administrative and configuration changes.

## Notes

Audit log exports are themselves audited, including the fields selected and the destination.

- **DOC-DEPLOY-002**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

---

## 3. VAL-0055

**Channel:** chat | **Customer plan:** business

**Subject:** 

**Ticket body:**

> we connecting our CI pipeline and not are sure whether to use personal key or something else. What is recommended approach for automation? please tell what to do.

**Draft reply:**

> For CI pipeline automation, the recommended approach is to create a service account rather than using a personal key [DOC-INT-001]. This ensures access survives staff changes, as keys issued to individual users are removed when that user is deleted [DOC-AUTH-004].
> 
> To set this up:
> 1. Create a service account for the pipeline [DOC-INT-001].
> 2. Grant the service account only the specific projects and permissions the pipeline needs, and review these grants when the pipeline changes [DOC-INT-001].
> 3. Store the credential as an encrypted secret in your pipeline provider; do not store it in the repository [DOC-INT-001].
> 4. Test the pipeline credential separately from deployment logic to distinguish authentication failures from deployment issues [DOC-INT-001].
> 
> Additionally, since service account keys do not expire by default, you should set an expiry and rotate them on a schedule [DOC-INT-001].

**Retrieved passages:**

- **DOC-INT-001 (cited)**, Connecting continuous integration pipelines: ## Resolution

1. Create a service account for the pipeline rather than using a personal key, so that access survives staff changes.
2. Grant the service account only the projects and permissions the pipeline needs, and review that grant when the pipeline changes.
3. Store the credential as an encrypted secret in your pipeline provider, never in the repository.
4. Test the pipeline credential separately from the deployment logic, so that authentication failures are distinguishable from deployment failures.

## Notes

Service account keys do not expire by default. Set an expiry and rotate on a schedule.

- **DOC-INT-001 (cited)**, Connecting continuous integration pipelines: # Connecting continuous integration pipelines

**Applies to:** All plans

## Symptoms

- The pipeline cannot authenticate against CloudServe
- Deployments succeed manually but fail from the pipeline
- The pipeline has broader access than intended

## Common causes

- A personal key was used rather than a service account
- The pipeline environment lacks the configuration present locally
- The service account was granted an organisation-wide role

## Resolution

- **DOC-AUTH-004 (cited)**, API key rotation and scope management: ## Resolution

1. Check the API keys page for the key's status and expiry. Revoked and expired keys are listed with the date and the user who acted.
2. Review the scopes attached to the key. Read-only keys cannot write, and project-scoped keys cannot reach organisation endpoints.
3. To rotate without downtime, create the replacement key first, deploy it, confirm traffic has moved, then revoke the old key.
4. If a key has been exposed publicly, revoke it immediately rather than waiting for the rotation window.

## Notes

Keys issued to individual users are removed when that user is deleted. Use service accounts for anything running in production.

- **DOC-AUTH-004 (cited)**, API key rotation and scope management: # API key rotation and scope management

**Applies to:** All plans

## Symptoms

- A previously working key returns 401 Unauthorized
- A key works for some endpoints and not others
- A key needs replacing after accidental exposure

## Common causes

- The key was revoked or reached its configured expiry
- The key was issued with a scope that excludes the endpoint being called
- The key belongs to a deleted user and was removed with the account

## Resolution

- **DOC-ONB-002**, Migrating an existing application to CloudServe: ## Resolution

1. Externalise configuration before migrating. Anything read from a file on disk should move to environment variables or secrets.
2. Identify local state such as uploaded files or session data and move it to object storage or the managed database first.
3. Run in parallel with the existing deployment and shift a small share of traffic before committing to the move.
4. Plan the database migration separately from the application migration; attempting both at once makes any failure hard to diagnose.

## Notes

Applications that write to the local filesystem will lose that data on every deployment and every scaling event.

---

## 4. VAL-0046

**Channel:** email | **Customer plan:** standard

**Subject:** How do I page through large results

**Ticket body:**

> when i do pagination some record coming two time and some missing. what is correct way?

**Draft reply:**

> Hi there,
> 
> To avoid missing or duplicating records when paginating through large results, you should use cursor pagination instead of offset pagination, especially if the data may change while you are iterating [DOC-API-002].
> 
> Here is the correct approach:
> 1. Use cursor pagination for any collection that might change during iteration [DOC-API-002].
> 2. Pass the `next_cursor` value from each response as the `cursor` parameter in your next request [DOC-API-002].
> 3. Stop paginating when the `next_cursor` value is null [DOC-API-002].
> 4. Keep your page size at or below 200 records, as larger requests are rejected [DOC-API-002].
> 
> Please note that cursors expire after one hour, so for long-running iterations, you should handle expiry by restarting from a recorded checkpoint [DOC-API-002]. If you are extracting very large datasets, consider using the export endpoint, which runs asynchronously and provides a download link [DOC-API-002].
> 
> Let us know if you need further assistance.

**Retrieved passages:**

- **DOC-API-002 (cited)**, Pagination and handling large result sets: # Pagination and handling large result sets

**Applies to:** All plans

## Symptoms

- Only the first page of results is returned
- Iterating through results misses or duplicates records
- Large queries time out

## Common causes

- The cursor from the previous response was not passed to the next request
- Offset pagination was used against a changing collection
- The page size requested exceeds the maximum

## Resolution

- **DOC-API-002 (cited)**, Pagination and handling large result sets: ## Resolution

1. Use cursor pagination for anything that may change while you iterate. Offset pagination will skip or repeat records when items are inserted mid-iteration.
2. Pass the next_cursor value from each response as the cursor parameter of the following request, and stop when it is null.
3. Keep page size at or below two hundred. Larger requests are rejected rather than truncated.
4. For very large extracts, use the export endpoint, which runs asynchronously and returns a download link.

## Notes

Cursors expire after one hour. Long-running iterations should handle expiry by restarting from a recorded checkpoint.

- **DOC-API-001**, Understanding API rate limits and quota tiers: ## Resolution

1. Read the rate limit headers returned with every response. They give the limit, the remaining allowance and the reset time, which is more reliable than inferring the limit from behaviour.
2. Confirm whether the endpoint has a specific limit. Search and export endpoints are more expensive and are limited more tightly than reads.
3. Implement exponential backoff with jitter on 429 responses rather than retrying immediately, which prolongs the throttling.
4. Where sustained higher throughput is genuinely required, the limit can be raised on Business and Enterprise plans through an account request.

## Notes

Limits are enforced per organisation. Issuing more keys does not increase the available quota.

- **DOC-INT-002**, Third party monitoring and log forwarding: ## Resolution

1. Check the forwarding status page, which shows the last successful delivery and any error returned by the destination.
2. Expect a delay of up to two minutes on metrics, since they are aggregated before being sent.
3. Apply a level filter at source so that debug output is not forwarded, which is usually the reason volume is higher than expected.
4. Verify the destination credential separately if delivery has stopped entirely, as expired credentials are the most common cause.

## Notes

Forwarding pauses after one hour of consecutive failures and must be resumed manually once the destination is healthy.

- **DOC-DATA-001**, Exporting account data and scheduled extracts: ## Resolution

1. Check the exports page for job status. Jobs covering more than a million records commonly take several minutes.
2. Request a fresh link from the exports page if the original has expired. The underlying file is retained for seven days.
3. Note that the export reflects the moment the job began, so records created during processing are not included.
4. For recurring needs, configure a scheduled export delivered to object storage rather than generating them manually.

## Notes

Exports containing personal data are logged in the audit trail with the requesting user and the fields included.

---

## 5. VAL-0044

**Channel:** chat | **Customer plan:** business

**Subject:** 

**Ticket body:**

> There are charges on our invoice for a service I do not believe we use. Could you explain what these relate to?

**Draft reply:**

> I can help you understand those charges. To identify what they relate to, please open the usage breakdown for the billing period, which itemises charges by service and by environment [DOC-BILL-001]. Look for resources in staging or development environments, as these are billed at the same rate as production [DOC-BILL-001]. Also, check the billing period dates at the top of the invoice, as the period runs from the anniversary of the subscription date rather than the calendar month [DOC-BILL-001]. If you would like to prevent unexpected charges in the future, you can set a usage alert on the billing page [DOC-BILL-001].

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-BILL-003**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

---

## 6. VAL-0026

**Channel:** email | **Customer plan:** business

**Subject:** Need data to stay in the EU

**Ticket body:**

> we need our data to remain within EU for contract we are signing. Our organisation created some time ago and i not sure which region it is in. please do the needful.

**Draft reply:**

> Hello,
> 
> To ensure your data remains within the EU, please first check the region displayed on your organisation settings page, as this is fixed at creation and determines where primary data is stored [DOC-DATA-003]. If your organisation was created in a region outside the EU, migrating it to an EU region requires a planned migration with support and involves a maintenance window [DOC-DATA-003].
> 
> Additionally, please review your backup replication settings, as cross-region replication is enabled by default and may need to be adjusted to meet single-region requirements [DOC-DATA-003]. Note that metadata such as account names and billing records is stored centrally regardless of the data region [DOC-DATA-003].
> 
> Please let us know if you would like to proceed with a region migration or need assistance reviewing your current settings.
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-DATA-003 (cited)**, Data residency and regional storage: # Data residency and regional storage

**Applies to:** Business and Enterprise plans

## Symptoms

- A customer requires data to remain in a specific region
- Latency is high for users far from the primary region
- A compliance review has asked where data is held

## Common causes

- The organisation was created in a region that no longer suits the requirement
- Read traffic is being served from the primary region only
- Backups are replicated to a second region by default

## Resolution

- **DOC-DATA-003 (cited)**, Data residency and regional storage: ## Resolution

1. Check the region shown on the organisation settings page. This is fixed at creation and determines where primary data is stored.
2. Enable read replicas in additional regions to reduce latency for distant users without moving primary storage.
3. Review the backup replication setting if a single-region requirement applies, since cross-region replication is enabled by default.
4. Migrating an organisation between regions requires a planned migration with support and involves a maintenance window.

## Notes

Metadata such as account names and billing records is stored centrally regardless of the data region.

- **DOC-SEC-003**, Audit logging and compliance evidence: ## Resolution

1. Filter the audit log by actor, resource and date range. Every administrative action carries the user, the address and the outcome.
2. Export the relevant period to object storage for anything needed beyond the retention window. Exports are not subject to retention limits.
3. Configure continuous export to your own storage if a policy requires retention longer than the plan provides.
4. Note that read access to resources is not logged on Business plans, only administrative and configuration changes.

## Notes

Audit log exports are themselves audited, including the fields selected and the destination.

- **DOC-DATA-001**, Exporting account data and scheduled extracts: ## Resolution

1. Check the exports page for job status. Jobs covering more than a million records commonly take several minutes.
2. Request a fresh link from the exports page if the original has expired. The underlying file is retained for seven days.
3. Note that the export reflects the moment the job began, so records created during processing are not included.
4. For recurring needs, configure a scheduled export delivered to object storage rather than generating them manually.

## Notes

Exports containing personal data are logged in the audit trail with the requesting user and the fields included.

- **DOC-ACCT-002**, Organisation setup and project structure: # Organisation setup and project structure

**Applies to:** All plans

## Symptoms

- Resources are difficult to separate for billing
- Environments are sharing configuration unintentionally
- A project needs moving between organisations

## Common causes

- Environments were created as folders within one project rather than as separate projects
- Configuration was set at organisation scope and inherited everywhere
- Projects cannot move between organisations without a migration

## Resolution

---

## 7. VAL-0033

**Channel:** forum | **Customer plan:** standard

**Subject:** Duplicate webhook deliveries

**Ticket body:**

> Signature verification fails for every delivery. We are computing the signature exactly as the documentation describes, over the parsed body.

**Draft reply:**

> Hi there, based on the documentation, the most likely cause of your signature verification failures is that the signature is being computed over the parsed body rather than the raw bytes. Re-serializing JSON changes the bytes and invalidates the signature. Please ensure you compute the signature over the raw request body before any parsing occurs. Additionally, since you are seeing duplicate deliveries, please make your handler idempotent using the event identifier, as at-least-once delivery means duplicates are expected. You can also check the webhook delivery log, which records every attempt with the response status and body for the last seven days, to help diagnose any other issues. [DOC-API-003]

**Retrieved passages:**

- **DOC-API-003 (cited)**, Webhook delivery, retries and signature verification: # Webhook delivery, retries and signature verification

**Applies to:** All plans

## Symptoms

- Webhooks are not arriving at the configured endpoint
- The same event is delivered more than once
- Signature verification fails

## Common causes

- The endpoint returned a non-2xx status and delivery is being retried
- The endpoint responded too slowly and the delivery timed out
- The signature was computed over a parsed body rather than the raw bytes

## Resolution

- **DOC-API-003 (cited)**, Webhook delivery, retries and signature verification: ## Resolution

1. Check the webhook delivery log, which records every attempt with the response status and body for the last seven days.
2. Return 2xx as quickly as possible and process the event asynchronously. Deliveries time out after five seconds.
3. Compute the signature over the raw request body before any parsing. Re-serialising JSON changes the bytes and invalidates the signature.
4. Make your handler idempotent using the event identifier. At-least-once delivery means duplicates are expected rather than exceptional.

## Notes

Failed deliveries are retried with backoff for twenty-four hours, after which the endpoint is disabled and the account is notified.

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: # Single sign-on configuration with SAML providers

**Applies to:** Business and Enterprise plans

## Symptoms

- Users are redirected to the identity provider and returned to an error page
- SSO works for some users and not others
- New users are not provisioned automatically

## Common causes

- The assertion consumer service URL does not match the value registered with CloudServe
- The email attribute in the assertion does not match the CloudServe account email
- Just-in-time provisioning is disabled on the connection

## Resolution

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: ## Resolution

1. Compare the assertion consumer service URL in your identity provider against the value shown on the SSO settings page. They must match exactly, including the trailing path.
2. Inspect a failing assertion and confirm the NameID is the user's email address in lower case.
3. Enable just-in-time provisioning if new users should be created on first login, and set a default role for provisioned users.
4. Keep at least one administrator account with password access while testing, so a misconfiguration does not lock the whole organisation out.

## Notes

SAML changes take effect immediately for new sessions but existing sessions remain valid until they expire.

- **DOC-INT-002**, Third party monitoring and log forwarding: ## Resolution

1. Check the forwarding status page, which shows the last successful delivery and any error returned by the destination.
2. Expect a delay of up to two minutes on metrics, since they are aggregated before being sent.
3. Apply a level filter at source so that debug output is not forwarded, which is usually the reason volume is higher than expected.
4. Verify the destination credential separately if delivery has stopped entirely, as expired credentials are the most common cause.

## Notes

Forwarding pauses after one hour of consecutive failures and must be resumed manually once the destination is healthy.

---

## 8. VAL-0072

**Channel:** docs_comment | **Customer plan:** standard

**Subject:** Invoice higher than expected

**Ticket body:**

> There are charges on our invoice for a service I do not believe we use. Could you explain what these relate to?

**Draft reply:**

> Hi there, I understand your concern about unexpected charges on your invoice. To help identify what these charges relate to, please open the usage breakdown for the billing period, which itemises charges by service and by environment [DOC-BILL-001]. It is common for resources left running in staging or development environments to be billed at the same rate as production, which can lead to unexpected costs [DOC-BILL-001]. Additionally, please check the billing period dates at the top of your invoice, as the period runs from the anniversary of your subscription date rather than the first of the month [DOC-BILL-001]. If you would like to prevent this in the future, you can set a usage alert on the billing page to notice unexpected accrual during the period [DOC-BILL-001]. If you believe an adjustment is needed, please note that invoices are finalised three days after the period ends, and adjustments requested before finalisation appear on the same invoice [DOC-BILL-001].

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-003**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

---

## 9. VAL-0056

**Channel:** email | **Customer plan:** standard

**Subject:** Build fails in the pipeline

**Ticket body:**

> Every deployment fails at the health check stage. I have increased the timeout twice already and it makes no difference.

**Draft reply:**

> Hi,
> 
> I understand that your deployments are failing at the health check stage, and that increasing the timeout has not resolved the issue. Based on the symptoms, this is often caused by a mismatch between the port the container is listening on and the port declared in the service definition, which can look like a timeout [DOC-DEPLOY-001].
> 
> Please try the following steps:
> 1. Confirm the container is listening on the port declared in the service definition [DOC-DEPLOY-001].
> 2. If your application needs time to warm up (e.g., loading models or caches), increase the initial delay rather than just the timeout; 30 seconds is a reasonable starting point [DOC-DEPLOY-001].
> 3. Compare the environment variables in the deployment against those required by your application, as missing configuration can cause silent startup failures [DOC-DEPLOY-001].
> 4. Inspect the container logs from the failed revision, as the rollback may replace the logs shown by default [DOC-DEPLOY-001].
> 
> Additionally, ensure your health check endpoint returns within the timeout using only local state, as endpoints that call a database can fail during incidents [DOC-DEPLOY-001].
> 
> Let me know if you need further assistance.

**Retrieved passages:**

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: # Container deployments failing during the health check phase

**Applies to:** Container Service

## Symptoms

- The deployment reaches running and then rolls back
- Logs show repeated health check timeouts
- The service works locally but not when deployed

## Common causes

- The health endpoint takes longer to respond than the configured timeout
- The container listens on a different port than the service declares
- A required environment variable is absent in the deployed environment

## Resolution

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: ## Resolution

1. Confirm the container is listening on the port declared in the service definition. A mismatch here produces a health check failure that looks like a timeout.
2. Increase the initial delay if the application needs time to warm up before it can answer. Thirty seconds is a reasonable starting point for services that load models or caches.
3. Compare the environment variables present in the deployment against those the application requires. Missing configuration frequently causes a silent startup failure.
4. Inspect the container logs from the failed revision rather than the running one; the rollback replaces the logs shown by default.

## Notes

- **DOC-ONB-001**, First deployment: a walkthrough: # First deployment: a walkthrough

**Applies to:** All plans

## Symptoms

- A new user does not know where to begin
- The first deployment fails for unclear reasons

## Common causes

- Required configuration has not been set
- The project structure does not match what the build expects

## Resolution

1. Create a project, then a service within it. Resources belong to services and services belong to projects.
2. Connect a repository or push a container image. The build service detects common project layouts automatically.
3. Set any environment variables the application needs before the first deployment rather than after it.
4. Deploy, then watch the logs for the first sixty seconds. Most first-deployment problems are visible immediately in startup output.

## Notes

- **DOC-DEPLOY-003**, Build failures caused by dependency resolution: # Build failures caused by dependency resolution

**Applies to:** Build Service

## Symptoms

- Builds that previously succeeded now fail without code changes
- The build works locally but fails in the pipeline
- Dependency resolution takes far longer than usual

## Common causes

- An unpinned dependency released a new incompatible version
- The build environment uses a different language runtime than the local machine
- The dependency cache holds a partially written artefact

## Resolution

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: ## Notes

A health check must return within the timeout using only local state. Endpoints that call a database will fail during a database incident and take the service down with them.

---

## 10. VAL-0013

**Channel:** docs_comment | **Customer plan:** business

**Subject:** Question about this month's charges

**Ticket body:**

> There are charges on our invoice for a service I do not believe we use. Could you explain what these relate to?

**Draft reply:**

> Hi there, 
> 
> I can help you understand the charges on your invoice. Charges for services you do not actively use can appear for a few reasons, such as usage-based charges accruing beyond your plan allowance, or resources being left running in non-production environments like staging or development, which are billed at the same rate as production [DOC-BILL-001]. Additionally, the billing period runs from the anniversary of your subscription date rather than the calendar month, which can sometimes cause confusion about when charges are applied [DOC-BILL-001]. 
> 
> To investigate, please open the usage breakdown for the period, which itemises charges by service and by environment [DOC-BILL-001]. Look specifically for resources in staging or development environments and check the billing period dates at the top of your invoice [DOC-BILL-001]. If you find any unexpected charges, you can also set a usage alert on the billing page to be notified during the period rather than at the end [DOC-BILL-001]. 
> 
> Please let me know if you need further assistance after reviewing the usage breakdown.

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-BILL-003**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

---

## 11. VAL-0051

**Channel:** forum | **Customer plan:** standard

**Subject:** Log forwarding stopped working

**Ticket body:**

> log forwarding to our external system stop two days ago and not resumed by itself. destination is healthy as we know. kindly check and revert.

**Draft reply:**

> Hi there, I understand that log forwarding to your external system stopped two days ago. Since you have confirmed the destination is healthy, the most likely cause is that the forwarding process paused after a period of consecutive failures and requires manual resumption [DOC-INT-002]. Additionally, expired credentials are a common cause for delivery stopping entirely, so please verify the destination credentials separately [DOC-INT-002]. To resolve this, please check the forwarding status page to see the last successful delivery and any error returned by the destination [DOC-INT-002]. If the status indicates a pause due to failures, you will need to manually resume the forwarding once the destination is confirmed healthy [DOC-INT-002].

**Retrieved passages:**

- **DOC-INT-002 (cited)**, Third party monitoring and log forwarding: # Third party monitoring and log forwarding

**Applies to:** Business and Enterprise plans

## Symptoms

- Logs are not arriving at the external destination
- Metrics are delayed compared with the console
- Forwarded volume is higher than expected

## Common causes

- The destination rejected the payload and forwarding paused
- Aggregation introduces a delay before metrics are forwarded
- Debug-level logs are being forwarded along with the rest

## Resolution

- **DOC-INT-002 (cited)**, Third party monitoring and log forwarding: ## Resolution

1. Check the forwarding status page, which shows the last successful delivery and any error returned by the destination.
2. Expect a delay of up to two minutes on metrics, since they are aggregated before being sent.
3. Apply a level filter at source so that debug output is not forwarded, which is usually the reason volume is higher than expected.
4. Verify the destination credential separately if delivery has stopped entirely, as expired credentials are the most common cause.

## Notes

Forwarding pauses after one hour of consecutive failures and must be resumed manually once the destination is healthy.

- **DOC-AUTH-001**, Resolving invalid credential errors on login: # Resolving invalid credential errors on login

**Applies to:** Console, CLI, SDK

## Symptoms

- The console returns 'Invalid credentials' despite a correct password
- Login succeeds in one browser but fails in another
- The CLI reports authentication failure after a working period

## Common causes

- The account is locked after five consecutive failed attempts
- A stale session cookie is being sent alongside new credentials
- The password was changed in another session and the client cached the old one

## Resolution

- **DOC-DEPLOY-001**, Container deployments failing during the health check phase: ## Resolution

1. Confirm the container is listening on the port declared in the service definition. A mismatch here produces a health check failure that looks like a timeout.
2. Increase the initial delay if the application needs time to warm up before it can answer. Thirty seconds is a reasonable starting point for services that load models or caches.
3. Compare the environment variables present in the deployment against those the application requires. Missing configuration frequently causes a silent startup failure.
4. Inspect the container logs from the failed revision rather than the running one; the rollback replaces the logs shown by default.

## Notes

- **DOC-SEC-003**, Audit logging and compliance evidence: # Audit logging and compliance evidence

**Applies to:** Business and Enterprise plans

## Symptoms

- An auditor has requested access records
- An event that should be logged cannot be found
- Log retention is shorter than a policy requires

## Common causes

- The event predates the retention window
- The event type is not covered by the audit log
- The organisation is on a plan with shorter retention

## Resolution

---

## 12. VAL-0040

**Channel:** email | **Customer plan:** business

**Subject:** Question about this month's charges

**Ticket body:**

> There are charges on our invoice for a service I do not believe we use. Could you explain what these relate to?

**Draft reply:**

> Hi there,
> 
> I can help explain the charges on your invoice. Charges for a service you do not believe you use can occur for a few reasons, such as usage-based charges accruing beyond your plan allowance, a resource being left running in a non-production environment, or the billing period running from your subscription date rather than the first of the month [DOC-BILL-001]. 
> 
> To identify the specific cause, please open the usage breakdown for the period, which itemises charges by service and by environment [DOC-BILL-001]. You should look for resources in staging or development environments, as these are billed at the same rate as production [DOC-BILL-001]. Additionally, check the billing period dates at the top of the invoice, as the period runs from the anniversary of your subscription date [DOC-BILL-001]. 
> 
> If you find that the charges are unexpected, please let me know the specific service or line item so I can assist you further. You can also set a usage alert on the billing page to notice unexpected accrual during the period rather than at the end of it [DOC-BILL-001].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-BILL-003**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

---

## 13. VAL-0005

**Channel:** chat | **Customer plan:** standard

**Subject:** 

**Ticket body:**

> Our cursor seems to stop working partway through a long iteration. Is there an expiry we should be handling?

**Draft reply:**

> Yes, cursors expire after one hour. For long-running iterations, you should handle this by restarting from a recorded checkpoint when the cursor expires. [DOC-API-002]

**Retrieved passages:**

- **DOC-API-002 (cited)**, Pagination and handling large result sets: ## Resolution

1. Use cursor pagination for anything that may change while you iterate. Offset pagination will skip or repeat records when items are inserted mid-iteration.
2. Pass the next_cursor value from each response as the cursor parameter of the following request, and stop when it is null.
3. Keep page size at or below two hundred. Larger requests are rejected rather than truncated.
4. For very large extracts, use the export endpoint, which runs asynchronously and returns a download link.

## Notes

Cursors expire after one hour. Long-running iterations should handle expiry by restarting from a recorded checkpoint.

- **DOC-DATA-002**, Backups, retention and point-in-time restore: ## Resolution

1. Identify the point you need to restore to. Point-in-time recovery covers any moment within the retention window rather than only backup times.
2. Restore into a new database instance rather than over the existing one, so the current state is preserved while you verify the restore.
3. Allow roughly ten minutes per hundred gigabytes for the restore, and considerably longer where the instance is also under load.
4. Verify the restored data before switching traffic, and keep the original instance until that verification is complete.

## Notes

Retention is seven days on Standard, thirty days on Business and ninety days on Enterprise plans.

- **DOC-DATA-001**, Exporting account data and scheduled extracts: ## Resolution

1. Check the exports page for job status. Jobs covering more than a million records commonly take several minutes.
2. Request a fresh link from the exports page if the original has expired. The underlying file is retained for seven days.
3. Note that the export reflects the moment the job began, so records created during processing are not included.
4. For recurring needs, configure a scheduled export delivered to object storage rather than generating them manually.

## Notes

Exports containing personal data are logged in the audit trail with the requesting user and the fields included.

- **DOC-AUTH-002**, Multi-factor authentication setup and recovery: ## Resolution

1. Ask the user to check that automatic time synchronisation is enabled on the device generating the code. Drift is the most common cause by a wide margin.
2. If the device is lost, the user should sign in with one of their recovery codes and then re-enrol a new device from the security page.
3. Where no recovery codes are available, an account administrator can reset multi-factor authentication for that user from the team members page.
4. If the user is the sole administrator and has no recovery codes, identity verification through support is required and takes up to one business day.

## Notes

Support cannot disable multi-factor authentication without identity verification, regardless of urgency.

- **DOC-API-001**, Understanding API rate limits and quota tiers: ## Resolution

1. Read the rate limit headers returned with every response. They give the limit, the remaining allowance and the reset time, which is more reliable than inferring the limit from behaviour.
2. Confirm whether the endpoint has a specific limit. Search and export endpoints are more expensive and are limited more tightly than reads.
3. Implement exponential backoff with jitter on 429 responses rather than retrying immediately, which prolongs the throttling.
4. Where sustained higher throughput is genuinely required, the limit can be raised on Business and Enterprise plans through an account request.

## Notes

Limits are enforced per organisation. Issuing more keys does not increase the available quota.

---

## 14. VAL-0076

**Channel:** email | **Customer plan:** standard

**Subject:** Need data to stay in the EU

**Ticket body:**

> We need our data to remain within the EU for a contract we are signing. Our organisation was created some time ago and I am not sure which region it is in.

**Draft reply:**

> Hi there,
> 
> To ensure your data remains within the EU, you first need to verify the region where your organisation was created, as this is fixed at creation and determines where primary data is stored [DOC-DATA-003]. You can check the current region on your organisation settings page [DOC-DATA-003].
> 
> If your organisation is currently in a non-EU region, migrating it to the EU requires a planned migration with support and involves a maintenance window [DOC-DATA-003]. Additionally, please note that backups are replicated to a second region by default, so you should review the backup replication setting to ensure it aligns with your single-region requirement [DOC-DATA-003].
> 
> Please note that metadata such as account names and billing records is stored centrally regardless of the data region [DOC-DATA-003].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-DATA-003 (cited)**, Data residency and regional storage: # Data residency and regional storage

**Applies to:** Business and Enterprise plans

## Symptoms

- A customer requires data to remain in a specific region
- Latency is high for users far from the primary region
- A compliance review has asked where data is held

## Common causes

- The organisation was created in a region that no longer suits the requirement
- Read traffic is being served from the primary region only
- Backups are replicated to a second region by default

## Resolution

- **DOC-DATA-003 (cited)**, Data residency and regional storage: ## Resolution

1. Check the region shown on the organisation settings page. This is fixed at creation and determines where primary data is stored.
2. Enable read replicas in additional regions to reduce latency for distant users without moving primary storage.
3. Review the backup replication setting if a single-region requirement applies, since cross-region replication is enabled by default.
4. Migrating an organisation between regions requires a planned migration with support and involves a maintenance window.

## Notes

Metadata such as account names and billing records is stored centrally regardless of the data region.

- **DOC-SEC-003**, Audit logging and compliance evidence: ## Resolution

1. Filter the audit log by actor, resource and date range. Every administrative action carries the user, the address and the outcome.
2. Export the relevant period to object storage for anything needed beyond the retention window. Exports are not subject to retention limits.
3. Configure continuous export to your own storage if a policy requires retention longer than the plan provides.
4. Note that read access to resources is not logged on Business plans, only administrative and configuration changes.

## Notes

Audit log exports are themselves audited, including the fields selected and the destination.

- **DOC-DATA-001**, Exporting account data and scheduled extracts: ## Resolution

1. Check the exports page for job status. Jobs covering more than a million records commonly take several minutes.
2. Request a fresh link from the exports page if the original has expired. The underlying file is retained for seven days.
3. Note that the export reflects the moment the job began, so records created during processing are not included.
4. For recurring needs, configure a scheduled export delivered to object storage rather than generating them manually.

## Notes

Exports containing personal data are logged in the audit trail with the requesting user and the fields included.

- **DOC-ACCT-002**, Organisation setup and project structure: # Organisation setup and project structure

**Applies to:** All plans

## Symptoms

- Resources are difficult to separate for billing
- Environments are sharing configuration unintentionally
- A project needs moving between organisations

## Common causes

- Environments were created as folders within one project rather than as separate projects
- Configuration was set at organisation scope and inherited everywhere
- Projects cannot move between organisations without a migration

## Resolution

---

## 15. VAL-0036

**Channel:** forum | **Customer plan:** business

**Subject:** Getting started with first deployment

**Ticket body:**

> Could you point me at the right starting place? I have created an account but the console has more in it than I expected.

**Draft reply:**

> Hi there, welcome to CloudServe. Since you have already created your account, the best starting point is the first deployment walkthrough. To get your first deployment running, you should first create a project and then a service within it, as resources belong to services and services belong to projects [DOC-ONB-001]. Next, connect a repository or push a container image; the build service will automatically detect common project layouts [DOC-ONB-001]. Before deploying, make sure to set any environment variables your application needs [DOC-ONB-001]. Once you deploy, watch the logs for the first sixty seconds, as most first-deployment issues are visible immediately in the startup output [DOC-ONB-001].

**Retrieved passages:**

- **DOC-ONB-001 (cited)**, First deployment: a walkthrough: # First deployment: a walkthrough

**Applies to:** All plans

## Symptoms

- A new user does not know where to begin
- The first deployment fails for unclear reasons

## Common causes

- Required configuration has not been set
- The project structure does not match what the build expects

## Resolution

1. Create a project, then a service within it. Resources belong to services and services belong to projects.
2. Connect a repository or push a container image. The build service detects common project layouts automatically.
3. Set any environment variables the application needs before the first deployment rather than after it.
4. Deploy, then watch the logs for the first sixty seconds. Most first-deployment problems are visible immediately in startup output.

## Notes

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: # Single sign-on configuration with SAML providers

**Applies to:** Business and Enterprise plans

## Symptoms

- Users are redirected to the identity provider and returned to an error page
- SSO works for some users and not others
- New users are not provisioned automatically

## Common causes

- The assertion consumer service URL does not match the value registered with CloudServe
- The email attribute in the assertion does not match the CloudServe account email
- Just-in-time provisioning is disabled on the connection

## Resolution

- **DOC-AUTH-001**, Resolving invalid credential errors on login: # Resolving invalid credential errors on login

**Applies to:** Console, CLI, SDK

## Symptoms

- The console returns 'Invalid credentials' despite a correct password
- Login succeeds in one browser but fails in another
- The CLI reports authentication failure after a working period

## Common causes

- The account is locked after five consecutive failed attempts
- A stale session cookie is being sent alongside new credentials
- The password was changed in another session and the client cached the old one

## Resolution

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: ## Resolution

1. Compare the assertion consumer service URL in your identity provider against the value shown on the SSO settings page. They must match exactly, including the trailing path.
2. Inspect a failing assertion and confirm the NameID is the user's email address in lower case.
3. Enable just-in-time provisioning if new users should be created on first login, and set a default role for provisioned users.
4. Keep at least one administrator account with password access while testing, so a misconfiguration does not lock the whole organisation out.

## Notes

SAML changes take effect immediately for new sessions but existing sessions remain valid until they expire.

- **DOC-INT-001**, Connecting continuous integration pipelines: # Connecting continuous integration pipelines

**Applies to:** All plans

## Symptoms

- The pipeline cannot authenticate against CloudServe
- Deployments succeed manually but fail from the pipeline
- The pipeline has broader access than intended

## Common causes

- A personal key was used rather than a service account
- The pipeline environment lacks the configuration present locally
- The service account was granted an organisation-wide role

## Resolution

---

## 16. VAL-0006

**Channel:** email | **Customer plan:** standard

**Subject:** MFA code keeps getting rejected

**Ticket body:**

> I have been trying to sign in for the last two hours and keep getting an invalid credentials message. I am certain the password is correct because I use a password manager. Nothing has changed at our end that I am aware of.

**Draft reply:**

> Hi there,
> 
> I understand you are experiencing issues signing in and receiving an 'invalid credentials' message despite using the correct password. Since you mentioned MFA in your subject line, this could be related to your multi-factor authentication setup or a general login issue.
> 
> If you are using an authenticator app for MFA, please check that automatic time synchronization is enabled on your device. Clock drift of more than thirty seconds is the most common cause for time-based codes being rejected as invalid [DOC-AUTH-002].
> 
> If you are not using an authenticator app, or if the issue persists after checking your device time, please note that accounts can become locked after five consecutive failed login attempts [DOC-AUTH-001]. Additionally, stale session cookies or cached old passwords from another session can also cause these errors [DOC-AUTH-001].
> 
> Could you please clarify if you are using an authenticator app for MFA, and if so, whether you have checked your device's time synchronization? This will help us determine the best next step to resolve your access issue.

**Retrieved passages:**

- **DOC-AUTH-002 (cited)**, Multi-factor authentication setup and recovery: # Multi-factor authentication setup and recovery

**Applies to:** All plans

## Symptoms

- The authenticator code is rejected as invalid
- A user has lost the device holding their authenticator
- Recovery codes were never downloaded

## Common causes

- Device clock drift of more than thirty seconds invalidates time-based codes
- The authenticator was enrolled against a different account
- Recovery codes were regenerated, invalidating the older set

## Resolution

- **DOC-AUTH-002 (cited)**, Multi-factor authentication setup and recovery: ## Resolution

1. Ask the user to check that automatic time synchronisation is enabled on the device generating the code. Drift is the most common cause by a wide margin.
2. If the device is lost, the user should sign in with one of their recovery codes and then re-enrol a new device from the security page.
3. Where no recovery codes are available, an account administrator can reset multi-factor authentication for that user from the team members page.
4. If the user is the sole administrator and has no recovery codes, identity verification through support is required and takes up to one business day.

## Notes

Support cannot disable multi-factor authentication without identity verification, regardless of urgency.

- **DOC-AUTH-001 (cited)**, Resolving invalid credential errors on login: # Resolving invalid credential errors on login

**Applies to:** Console, CLI, SDK

## Symptoms

- The console returns 'Invalid credentials' despite a correct password
- Login succeeds in one browser but fails in another
- The CLI reports authentication failure after a working period

## Common causes

- The account is locked after five consecutive failed attempts
- A stale session cookie is being sent alongside new credentials
- The password was changed in another session and the client cached the old one

## Resolution

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: ## Resolution

1. Compare the assertion consumer service URL in your identity provider against the value shown on the SSO settings page. They must match exactly, including the trailing path.
2. Inspect a failing assertion and confirm the NameID is the user's email address in lower case.
3. Enable just-in-time provisioning if new users should be created on first login, and set a default role for provisioned users.
4. Keep at least one administrator account with password access while testing, so a misconfiguration does not lock the whole organisation out.

## Notes

SAML changes take effect immediately for new sessions but existing sessions remain valid until they expire.

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: # Single sign-on configuration with SAML providers

**Applies to:** Business and Enterprise plans

## Symptoms

- Users are redirected to the identity provider and returned to an error page
- SSO works for some users and not others
- New users are not provisioned automatically

## Common causes

- The assertion consumer service URL does not match the value registered with CloudServe
- The email attribute in the assertion does not match the CloudServe account email
- Just-in-time provisioning is disabled on the connection

## Resolution

---

## 17. VAL-0078

**Channel:** docs_comment | **Customer plan:** business

**Subject:** Database restore taking hours

**Ticket body:**

> connection not available error coming. we scale up service then problem start. please check.

**Draft reply:**

> Hi there, 
> 
> I understand you are experiencing a 'connection not available' error and that the database restore is taking several hours after scaling up your service. 
> 
> Based on the symptoms, this is likely related to database connection pool exhaustion. This can occur when the pool size multiplied by the instance count exceeds the database connection limit, or when connections are not being returned to the pool after use [DOC-PERF-003]. Scaling up your service increases the instance count, which can easily push the total connection demand over the limit if the pool size is not adjusted accordingly [DOC-PERF-003]. 
> 
> Regarding the restore time, please note that restore time scales with database size, and you should allow roughly ten minutes per hundred gigabytes for the restore, with considerably longer times if the instance is also under load [DOC-DATA-002]. 
> 
> To resolve the connection issue, please review your connection pool settings to ensure the total connections do not exceed your database's limit, and check for any long-running transactions holding connections open [DOC-PERF-003]. 
> 
> Please let me know if you need further assistance.

**Retrieved passages:**

- **DOC-DATA-002 (cited)**, Backups, retention and point-in-time restore: ## Resolution

1. Identify the point you need to restore to. Point-in-time recovery covers any moment within the retention window rather than only backup times.
2. Restore into a new database instance rather than over the existing one, so the current state is preserved while you verify the restore.
3. Allow roughly ten minutes per hundred gigabytes for the restore, and considerably longer where the instance is also under load.
4. Verify the restored data before switching traffic, and keep the original instance until that verification is complete.

## Notes

Retention is seven days on Standard, thirty days on Business and ninety days on Enterprise plans.

- **DOC-PERF-003 (cited)**, Database connection pool exhaustion: # Database connection pool exhaustion

**Applies to:** Managed Database

## Symptoms

- Errors indicating no connection is available
- Latency increases sharply as traffic grows
- The database reports far fewer active queries than the application expects

## Common causes

- The pool size multiplied by the instance count exceeds the database connection limit
- Connections are not being returned to the pool after use
- Long-running transactions are holding connections open

## Resolution

- **DOC-DEPLOY-001**, Container deployments failing during the health check phase: ## Resolution

1. Confirm the container is listening on the port declared in the service definition. A mismatch here produces a health check failure that looks like a timeout.
2. Increase the initial delay if the application needs time to warm up before it can answer. Thirty seconds is a reasonable starting point for services that load models or caches.
3. Compare the environment variables present in the deployment against those the application requires. Missing configuration frequently causes a silent startup failure.
4. Inspect the container logs from the failed revision rather than the running one; the rollback replaces the logs shown by default.

## Notes

- **DOC-DATA-002 (cited)**, Backups, retention and point-in-time restore: # Backups, retention and point-in-time restore

**Applies to:** Managed Database

## Symptoms

- Data was deleted and needs recovering
- A restore is taking longer than expected
- A backup is older than expected

## Common causes

- Automated backups run daily and retention depends on the plan
- Restore time scales with database size
- Point-in-time recovery is available only where continuous archiving is enabled

## Resolution

- **DOC-DEPLOY-002**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

---

## 18. VAL-0038

**Channel:** forum | **Customer plan:** standard

**Subject:** p95 latency is very high

**Ticket body:**

> Our response times have roughly doubled since two days ago with no deployment on our side. The median looks acceptable but the 95th percentile is far worse than it was.

**Draft reply:**

> Hi there, I'm sorry to hear your response times have doubled. Since you haven't deployed any changes, this often points to resource contention or downstream issues rather than code problems. 
> 
> To diagnose this, please check the following:
> 1. Compare your median and 95th percentile latency on the metrics page. A large gap suggests contention or queueing [DOC-PERF-001].
> 2. Check memory utilization across your instances. Sustained usage above 80% often causes latency spikes before failures [DOC-PERF-001].
> 3. Review the dependency timing breakdown in the trace view to see if the delay is in your service or a downstream dependency [DOC-PERF-001].
> 4. If your load is predictable, consider adjusting your autoscaling policy to scale on request count rather than processor utilization for a faster response [DOC-PERF-001].
> 
> Also, keep in mind that frequent scaling events can raise the 95th percentile due to cold starts, even if the service itself is healthy [DOC-PERF-001].

**Retrieved passages:**

- **DOC-PERF-001 (cited)**, Diagnosing elevated response latency: # Diagnosing elevated response latency

**Applies to:** All compute services

## Symptoms

- Response times have increased without a code change
- The 95th percentile is far above the median
- Latency rises at predictable times of day

## Common causes

- The service is running close to its memory limit and spending time in garbage collection
- A downstream dependency has slowed and the delay is propagating
- Instance count is not scaling with the load pattern

## Resolution

- **DOC-PERF-001 (cited)**, Diagnosing elevated response latency: ## Resolution

1. Compare median and 95th percentile latency on the metrics page. A large gap points to contention or queueing rather than a uniformly slower service.
2. Check memory utilisation across instances. Sustained utilisation above eighty per cent typically shows up as latency before it shows up as failure.
3. Review the dependency timing breakdown on the trace view to identify whether the time is being spent in your service or waiting on another.
4. Adjust the autoscaling policy if load is predictable. Scaling on request count responds sooner than scaling on processor utilisation.

## Notes

Cold starts affect the first request to a new instance. Frequent scaling events will therefore raise the 95th percentile even when the service itself is healthy.

- **DOC-INT-002**, Third party monitoring and log forwarding: ## Resolution

1. Check the forwarding status page, which shows the last successful delivery and any error returned by the destination.
2. Expect a delay of up to two minutes on metrics, since they are aggregated before being sent.
3. Apply a level filter at source so that debug output is not forwarded, which is usually the reason volume is higher than expected.
4. Verify the destination credential separately if delivery has stopped entirely, as expired credentials are the most common cause.

## Notes

Forwarding pauses after one hour of consecutive failures and must be resumed manually once the destination is healthy.

- **DOC-API-001**, Understanding API rate limits and quota tiers: # Understanding API rate limits and quota tiers

**Applies to:** All plans

## Symptoms

- Requests return 429 Too Many Requests
- Throughput drops sharply at a predictable point
- Limits appear lower than the documented figure

## Common causes

- The limit applies per organisation rather than per key
- Burst capacity was consumed and the sustained rate now applies
- The endpoint being called has a lower limit than the general one

## Resolution

- **DOC-API-001**, Understanding API rate limits and quota tiers: ## Resolution

1. Read the rate limit headers returned with every response. They give the limit, the remaining allowance and the reset time, which is more reliable than inferring the limit from behaviour.
2. Confirm whether the endpoint has a specific limit. Search and export endpoints are more expensive and are limited more tightly than reads.
3. Implement exponential backoff with jitter on 429 responses rather than retrying immediately, which prolongs the throttling.
4. Where sustained higher throughput is genuinely required, the limit can be raised on Business and Enterprise plans through an account request.

## Notes

Limits are enforced per organisation. Issuing more keys does not increase the available quota.

---

## 19. VAL-0024

**Channel:** chat | **Customer plan:** standard

**Subject:** 

**Ticket body:**

> A key can read fine but every write returns a permission error. I created it myself and I thought I gave it full access.

**Draft reply:**

> Hi there, I can help with that. Since the key can read but fails on writes, the issue is likely related to the specific scopes attached to the key rather than the key being revoked or expired. Please check the API keys page to review the scopes attached to your key. Read-only keys cannot perform write operations, and project-scoped keys cannot reach organisation endpoints. If the key is missing the necessary write permissions, you may need to create a new key with the correct scopes, deploy it, and then revoke the old one to avoid downtime. [DOC-AUTH-004]

**Retrieved passages:**

- **DOC-AUTH-004 (cited)**, API key rotation and scope management: ## Resolution

1. Check the API keys page for the key's status and expiry. Revoked and expired keys are listed with the date and the user who acted.
2. Review the scopes attached to the key. Read-only keys cannot write, and project-scoped keys cannot reach organisation endpoints.
3. To rotate without downtime, create the replacement key first, deploy it, confirm traffic has moved, then revoke the old key.
4. If a key has been exposed publicly, revoke it immediately rather than waiting for the rotation window.

## Notes

Keys issued to individual users are removed when that user is deleted. Use service accounts for anything running in production.

- **DOC-AUTH-004 (cited)**, API key rotation and scope management: # API key rotation and scope management

**Applies to:** All plans

## Symptoms

- A previously working key returns 401 Unauthorized
- A key works for some endpoints and not others
- A key needs replacing after accidental exposure

## Common causes

- The key was revoked or reached its configured expiry
- The key was issued with a scope that excludes the endpoint being called
- The key belongs to a deleted user and was removed with the account

## Resolution

- **DOC-AUTH-002**, Multi-factor authentication setup and recovery: ## Resolution

1. Ask the user to check that automatic time synchronisation is enabled on the device generating the code. Drift is the most common cause by a wide margin.
2. If the device is lost, the user should sign in with one of their recovery codes and then re-enrol a new device from the security page.
3. Where no recovery codes are available, an account administrator can reset multi-factor authentication for that user from the team members page.
4. If the user is the sole administrator and has no recovery codes, identity verification through support is required and takes up to one business day.

## Notes

Support cannot disable multi-factor authentication without identity verification, regardless of urgency.

- **DOC-AUTH-001**, Resolving invalid credential errors on login: ## Resolution

1. Confirm whether the account is locked by checking the security page of the console. A locked account displays a red banner and unlocks automatically after thirty minutes.
2. Clear cookies for the CloudServe domain, or open a private browsing window, then attempt the login again.
3. If the CLI is failing, run `cloudserve auth logout` followed by `cloudserve auth login` to discard the cached token.
4. Where the account remains locked and the customer needs immediate access, an administrator on the account can release the lock from the team members page.

## Notes

Repeated lockouts within a short period usually indicate an automated process still using an old password rather than a user error.

- **DOC-ACCT-001**, Managing team members, roles and permissions: # Managing team members, roles and permissions

**Applies to:** All plans

## Symptoms

- A user cannot access a project they should be able to
- A departing user needs removing
- Permissions need narrowing after a review

## Common causes

- The role was granted at project scope rather than organisation scope
- The invitation was never accepted and the account does not exist
- A group membership grants broader access than the direct role suggests

## Resolution

---

## 20. VAL-0021

**Channel:** chat | **Customer plan:** standard

**Subject:** 

**Ticket body:**

> We shipped a release earlier today that has broken checkout for a portion of our customers. We need to get back to the previous version quickly. What is the fastest safe route?

**Draft reply:**

> The fastest safe route is to roll back to the last healthy revision. Open the revisions page for the service, identify the last healthy revision, and select roll back. Traffic moves within roughly thirty seconds and no rebuild takes place [DOC-DEPLOY-002]. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect [DOC-DEPLOY-002]. Note that rollback restores the container image and its configuration together, but it does not restore data [DOC-DEPLOY-002]. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh [DOC-DEPLOY-002].

**Retrieved passages:**

- **DOC-DEPLOY-002 (cited)**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

- **DOC-DEPLOY-002 (cited)**, Rolling back a failed release: # Rolling back a failed release

**Applies to:** Container Service, Functions

## Symptoms

- A release has introduced errors and must be reverted
- The previous revision is needed while a fix is prepared

## Common causes

- A defect reached production that testing did not catch
- A configuration change had unintended effects

## Resolution

- **DOC-DATA-002**, Backups, retention and point-in-time restore: ## Resolution

1. Identify the point you need to restore to. Point-in-time recovery covers any moment within the retention window rather than only backup times.
2. Restore into a new database instance rather than over the existing one, so the current state is preserved while you verify the restore.
3. Allow roughly ten minutes per hundred gigabytes for the restore, and considerably longer where the instance is also under load.
4. Verify the restored data before switching traffic, and keep the original instance until that verification is complete.

## Notes

Retention is seven days on Standard, thirty days on Business and ninety days on Enterprise plans.

- **DOC-API-003**, Webhook delivery, retries and signature verification: ## Resolution

1. Check the webhook delivery log, which records every attempt with the response status and body for the last seven days.
2. Return 2xx as quickly as possible and process the event asynchronously. Deliveries time out after five seconds.
3. Compute the signature over the raw request body before any parsing. Re-serialising JSON changes the bytes and invalidates the signature.
4. Make your handler idempotent using the event identifier. At-least-once delivery means duplicates are expected rather than exceptional.

## Notes

Failed deliveries are retried with backoff for twenty-four hours, after which the endpoint is disabled and the account is notified.

- **DOC-INT-002**, Third party monitoring and log forwarding: ## Resolution

1. Check the forwarding status page, which shows the last successful delivery and any error returned by the destination.
2. Expect a delay of up to two minutes on metrics, since they are aggregated before being sent.
3. Apply a level filter at source so that debug output is not forwarded, which is usually the reason volume is higher than expected.
4. Verify the destination credential separately if delivery has stopped entirely, as expired credentials are the most common cause.

## Notes

Forwarding pauses after one hour of consecutive failures and must be resumed manually once the destination is healthy.

---

## 21. VAL-0025

**Channel:** chat | **Customer plan:** business

**Subject:** 

**Ticket body:**

> every deployment fails at health check stage. i am having increase timeout twice already and it makes no difference. kindly check and revert.

**Draft reply:**

> Hi, I understand that your deployments are failing at the health check stage and that increasing the timeout has not resolved the issue. Based on our documentation, here are a few specific areas to check that often cause this behavior:
> 
> 1. **Port Mismatch:** Confirm that the container is listening on the exact port declared in your service definition. A mismatch here often produces a health check failure that looks like a timeout [DOC-DEPLOY-001].
> 2. **Environment Variables:** Compare the environment variables present in the deployment against those your application requires. Missing configuration can cause a silent startup failure, preventing the health check from succeeding [DOC-DEPLOY-001].
> 3. **Log Inspection:** Please inspect the container logs from the *failed* revision rather than the running one, as the rollback process replaces the logs shown by default [DOC-DEPLOY-001].
> 4. **Health Check Logic:** Ensure your health check endpoint returns within the timeout using only local state. If the endpoint calls a database, it may fail during incidents and take the service down [DOC-DEPLOY-001].
> 
> If you have verified the port and environment variables, please share the logs from the failed revision so we can investigate further.

**Retrieved passages:**

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: # Container deployments failing during the health check phase

**Applies to:** Container Service

## Symptoms

- The deployment reaches running and then rolls back
- Logs show repeated health check timeouts
- The service works locally but not when deployed

## Common causes

- The health endpoint takes longer to respond than the configured timeout
- The container listens on a different port than the service declares
- A required environment variable is absent in the deployed environment

## Resolution

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: ## Resolution

1. Confirm the container is listening on the port declared in the service definition. A mismatch here produces a health check failure that looks like a timeout.
2. Increase the initial delay if the application needs time to warm up before it can answer. Thirty seconds is a reasonable starting point for services that load models or caches.
3. Compare the environment variables present in the deployment against those the application requires. Missing configuration frequently causes a silent startup failure.
4. Inspect the container logs from the failed revision rather than the running one; the rollback replaces the logs shown by default.

## Notes

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: ## Notes

A health check must return within the timeout using only local state. Endpoints that call a database will fail during a database incident and take the service down with them.

- **DOC-ONB-001**, First deployment: a walkthrough: # First deployment: a walkthrough

**Applies to:** All plans

## Symptoms

- A new user does not know where to begin
- The first deployment fails for unclear reasons

## Common causes

- Required configuration has not been set
- The project structure does not match what the build expects

## Resolution

1. Create a project, then a service within it. Resources belong to services and services belong to projects.
2. Connect a repository or push a container image. The build service detects common project layouts automatically.
3. Set any environment variables the application needs before the first deployment rather than after it.
4. Deploy, then watch the logs for the first sixty seconds. Most first-deployment problems are visible immediately in startup output.

## Notes

- **DOC-DEPLOY-002**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

---

## 22. VAL-0074

**Channel:** docs_comment | **Customer plan:** standard

**Subject:** Remove a departing team member

**Ticket body:**

> We are tightening permissions after a review and I want to understand how group membership interacts with directly assigned roles.

**Draft reply:**

> Hi there,
> 
> To understand how group membership interacts with directly assigned roles, you should check the effective permissions view for the user. This view resolves direct roles and group memberships together to show the final access level [DOC-ACCT-001]. 
> 
> When managing permissions, it is generally recommended to prefer group membership over direct role assignment, as this allows access to be reviewed in one place [DOC-ACCT-001]. If you are removing a departing team member, ensure you remove the user rather than just changing their password, and revoke any API keys they created [DOC-ACCT-001]. Note that removing the last account owner is not permitted; ownership must be transferred before removal [DOC-ACCT-001].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-ACCT-001 (cited)**, Managing team members, roles and permissions: # Managing team members, roles and permissions

**Applies to:** All plans

## Symptoms

- A user cannot access a project they should be able to
- A departing user needs removing
- Permissions need narrowing after a review

## Common causes

- The role was granted at project scope rather than organisation scope
- The invitation was never accepted and the account does not exist
- A group membership grants broader access than the direct role suggests

## Resolution

- **DOC-ACCT-001 (cited)**, Managing team members, roles and permissions: ## Resolution

1. Check the effective permissions view for the user, which resolves direct roles and group memberships together.
2. Confirm the invitation was accepted. Pending invitations appear in a separate section and expire after seven days.
3. Remove a departing user rather than only changing their password, and revoke any API keys they created.
4. Prefer group membership to direct role assignment, so that access can be reviewed in one place.

## Notes

Removing the last account owner is not permitted. Transfer ownership before removing the account.

- **DOC-SEC-001**, Responding to a suspected account compromise: ## Resolution

1. Revoke all API keys for the affected account immediately. This is disruptive and it is the correct first action.
2. Force a password reset and terminate active sessions for the affected users from the team members page.
3. Review the audit log for the period in question, filtering by the affected user, and record anything unexpected before it ages out.
4. Enable multi-factor authentication for all users if it is not already mandatory for the organisation.

## Notes

Audit logs are retained for ninety days on Business plans and one year on Enterprise. Export them promptly during an investigation.

- **DOC-SEC-001**, Responding to a suspected account compromise: # Responding to a suspected account compromise

**Applies to:** All plans

## Symptoms

- Unrecognised activity appears in the audit log
- A user reports credentials may have been exposed
- Resources were created that nobody claims

## Common causes

- Credentials were reused from a service that suffered a breach
- An API key was committed to a public repository
- A former team member retained access after leaving

## Resolution

- **DOC-AUTH-004**, API key rotation and scope management: ## Resolution

1. Check the API keys page for the key's status and expiry. Revoked and expired keys are listed with the date and the user who acted.
2. Review the scopes attached to the key. Read-only keys cannot write, and project-scoped keys cannot reach organisation endpoints.
3. To rotate without downtime, create the replacement key first, deploy it, confirm traffic has moved, then revoke the old key.
4. If a key has been exposed publicly, revoke it immediately rather than waiting for the rotation window.

## Notes

Keys issued to individual users are removed when that user is deleted. Use service accounts for anything running in production.

---

## 23. VAL-0023

**Channel:** email | **Customer plan:** business

**Subject:** Migrating our app across

**Ticket body:**

> We have just signed up and I am not sure where to start. We have a containerised application and would like to get it deployed.

**Draft reply:**

> Hi there,
> 
> Welcome to CloudServe. Since you have a containerised application, the fastest path to your first deployment is to create a project and a service within it, then push your container image to the service [DOC-ONB-001]. Before you deploy, make sure any required environment variables are set, as missing configuration is a common cause of first-deployment failures [DOC-ONB-001].
> 
> Because you are migrating an existing application, please also ensure that any configuration currently read from files on disk is moved to environment variables or secrets, and that any local state (such as uploaded files or session data) is moved to object storage or a managed database [DOC-ONB-002]. This is important because applications that write to the local filesystem will lose that data on every deployment and scaling event [DOC-ONB-002].
> 
> Once deployed, watch the logs for the first sixty seconds to catch any immediate startup issues [DOC-ONB-001]. If you encounter health check failures, verify that your container is listening on the port declared in the service definition and that all required environment variables are present [DOC-DEPLOY-001].
> 
> Let us know if you need help with any of these steps.
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-ONB-002 (cited)**, Migrating an existing application to CloudServe: ## Resolution

1. Externalise configuration before migrating. Anything read from a file on disk should move to environment variables or secrets.
2. Identify local state such as uploaded files or session data and move it to object storage or the managed database first.
3. Run in parallel with the existing deployment and shift a small share of traffic before committing to the move.
4. Plan the database migration separately from the application migration; attempting both at once makes any failure hard to diagnose.

## Notes

Applications that write to the local filesystem will lose that data on every deployment and every scaling event.

- **DOC-ONB-002 (cited)**, Migrating an existing application to CloudServe: # Migrating an existing application to CloudServe

**Applies to:** All plans

## Symptoms

- An existing application needs moving with minimal downtime
- The application depends on services not yet available

## Common causes

- Configuration is embedded in the application rather than externalised
- The application depends on local state that will not survive scaling

## Resolution

- **DOC-ONB-001 (cited)**, First deployment: a walkthrough: # First deployment: a walkthrough

**Applies to:** All plans

## Symptoms

- A new user does not know where to begin
- The first deployment fails for unclear reasons

## Common causes

- Required configuration has not been set
- The project structure does not match what the build expects

## Resolution

1. Create a project, then a service within it. Resources belong to services and services belong to projects.
2. Connect a repository or push a container image. The build service detects common project layouts automatically.
3. Set any environment variables the application needs before the first deployment rather than after it.
4. Deploy, then watch the logs for the first sixty seconds. Most first-deployment problems are visible immediately in startup output.

## Notes

- **DOC-DEPLOY-002**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: ## Resolution

1. Confirm the container is listening on the port declared in the service definition. A mismatch here produces a health check failure that looks like a timeout.
2. Increase the initial delay if the application needs time to warm up before it can answer. Thirty seconds is a reasonable starting point for services that load models or caches.
3. Compare the environment variables present in the deployment against those the application requires. Missing configuration frequently causes a silent startup failure.
4. Inspect the container logs from the failed revision rather than the running one; the rollback replaces the logs shown by default.

## Notes

---

## 24. VAL-0049

**Channel:** email | **Customer plan:** enterprise

**Subject:** Need to rotate an exposed key

**Ticket body:**

> key can read fine but every write returns permission error. I created it myself and I thought I gave it full access. please help fast.

**Draft reply:**

> Hi there,
> 
> I understand you are experiencing permission errors on write operations and need to rotate an exposed key. Please do not send the live credential in this ticket, as any credential shared in a support ticket must be treated as exposed [DOC-SEC-002].
> 
> To resolve the permission errors and handle the exposure, please follow these steps:
> 
> 1. Revoke the exposed key immediately rather than waiting for a standard rotation window [DOC-AUTH-004].
> 2. Review the scopes attached to your keys. Read-only keys cannot write, and project-scoped keys cannot reach organisation endpoints, which likely explains why reads work but writes fail [DOC-AUTH-004].
> 3. Issue a replacement key with the narrowest scope that still works for your needs, rather than recreating the original permissions by default [DOC-SEC-002].
> 4. To avoid downtime, create the replacement key first, deploy it, confirm traffic has moved, and then ensure the old key is revoked [DOC-AUTH-004].
> 5. Search the audit log for use of the exposed credential from unfamiliar addresses during the exposure window [DOC-SEC-002].
> 
> Let us know if you need further assistance.

**Retrieved passages:**

- **DOC-AUTH-004 (cited)**, API key rotation and scope management: ## Resolution

1. Check the API keys page for the key's status and expiry. Revoked and expired keys are listed with the date and the user who acted.
2. Review the scopes attached to the key. Read-only keys cannot write, and project-scoped keys cannot reach organisation endpoints.
3. To rotate without downtime, create the replacement key first, deploy it, confirm traffic has moved, then revoke the old key.
4. If a key has been exposed publicly, revoke it immediately rather than waiting for the rotation window.

## Notes

Keys issued to individual users are removed when that user is deleted. Use service accounts for anything running in production.

- **DOC-AUTH-004 (cited)**, API key rotation and scope management: # API key rotation and scope management

**Applies to:** All plans

## Symptoms

- A previously working key returns 401 Unauthorized
- A key works for some endpoints and not others
- A key needs replacing after accidental exposure

## Common causes

- The key was revoked or reached its configured expiry
- The key was issued with a scope that excludes the endpoint being called
- The key belongs to a deleted user and was removed with the account

## Resolution

- **DOC-SEC-002 (cited)**, Handling exposed secrets and credential rotation: # Handling exposed secrets and credential rotation

**Applies to:** All plans

## Symptoms

- A key has been committed to a repository
- A secret appears in application logs
- A third party has reported finding a credential

## Common causes

- Configuration was committed rather than referenced from the environment
- The application prints its configuration during startup
- A key was shared in a support ticket or a chat message

## Resolution

- **DOC-SEC-002 (cited)**, Handling exposed secrets and credential rotation: ## Resolution

1. Revoke the exposed credential first. Removing it from the repository does not help, because it remains in the history.
2. Issue a replacement with the narrowest scope that still works, rather than recreating the original permissions by default.
3. Search the audit log for use of the exposed credential from unfamiliar addresses during the exposure window.
4. Add secret scanning to your pipeline so that the next occurrence is caught before it reaches a remote branch.

## Notes

Never send a live credential to support. Support will never ask for one, and any credential shared in a ticket must be treated as exposed.

- **DOC-SEC-001**, Responding to a suspected account compromise: ## Resolution

1. Revoke all API keys for the affected account immediately. This is disruptive and it is the correct first action.
2. Force a password reset and terminate active sessions for the affected users from the team members page.
3. Review the audit log for the period in question, filtering by the affected user, and record anything unexpected before it ages out.
4. Enable multi-factor authentication for all users if it is not already mandatory for the organisation.

## Notes

Audit logs are retained for ninety days on Business plans and one year on Enterprise. Export them promptly during an investigation.

---

## 25. VAL-0061

**Channel:** email | **Customer plan:** standard

**Subject:** Webhooks not arriving

**Ticket body:**

> Signature verification fails for every delivery. We are computing the signature exactly as the documentation describes, over the parsed body.

**Draft reply:**

> Hi,
> 
> Thanks for reaching out. Based on your description, the issue is likely caused by computing the signature over the parsed body rather than the raw bytes [DOC-API-003]. Re-serialising JSON changes the bytes and invalidates the signature [DOC-API-003].
> 
> Please ensure you compute the signature over the raw request body before any parsing [DOC-API-003]. Additionally, verify that your endpoint returns a 2xx status as quickly as possible, as deliveries time out after five seconds [DOC-API-003]. You can check the webhook delivery log for the last seven days to review response statuses and bodies [DOC-API-003].
> 
> Let us know if this resolves the issue.
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-API-003 (cited)**, Webhook delivery, retries and signature verification: # Webhook delivery, retries and signature verification

**Applies to:** All plans

## Symptoms

- Webhooks are not arriving at the configured endpoint
- The same event is delivered more than once
- Signature verification fails

## Common causes

- The endpoint returned a non-2xx status and delivery is being retried
- The endpoint responded too slowly and the delivery timed out
- The signature was computed over a parsed body rather than the raw bytes

## Resolution

- **DOC-API-003 (cited)**, Webhook delivery, retries and signature verification: ## Resolution

1. Check the webhook delivery log, which records every attempt with the response status and body for the last seven days.
2. Return 2xx as quickly as possible and process the event asynchronously. Deliveries time out after five seconds.
3. Compute the signature over the raw request body before any parsing. Re-serialising JSON changes the bytes and invalidates the signature.
4. Make your handler idempotent using the event identifier. At-least-once delivery means duplicates are expected rather than exceptional.

## Notes

Failed deliveries are retried with backoff for twenty-four hours, after which the endpoint is disabled and the account is notified.

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: # Single sign-on configuration with SAML providers

**Applies to:** Business and Enterprise plans

## Symptoms

- Users are redirected to the identity provider and returned to an error page
- SSO works for some users and not others
- New users are not provisioned automatically

## Common causes

- The assertion consumer service URL does not match the value registered with CloudServe
- The email attribute in the assertion does not match the CloudServe account email
- Just-in-time provisioning is disabled on the connection

## Resolution

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: ## Resolution

1. Compare the assertion consumer service URL in your identity provider against the value shown on the SSO settings page. They must match exactly, including the trailing path.
2. Inspect a failing assertion and confirm the NameID is the user's email address in lower case.
3. Enable just-in-time provisioning if new users should be created on first login, and set a default role for provisioned users.
4. Keep at least one administrator account with password access while testing, so a misconfiguration does not lock the whole organisation out.

## Notes

SAML changes take effect immediately for new sessions but existing sessions remain valid until they expire.

- **DOC-INT-001**, Connecting continuous integration pipelines: # Connecting continuous integration pipelines

**Applies to:** All plans

## Symptoms

- The pipeline cannot authenticate against CloudServe
- Deployments succeed manually but fail from the pipeline
- The pipeline has broader access than intended

## Common causes

- A personal key was used rather than a service account
- The pipeline environment lacks the configuration present locally
- The service account was granted an organisation-wide role

## Resolution

---

## 26. VAL-0042

**Channel:** chat | **Customer plan:** business

**Subject:** 

**Ticket body:**

> Our staging environment is picking up production configuration values. I cannot work out where the override is coming from.

**Draft reply:**

> Hi there, I can help you track down where the production configuration values are coming from in your staging environment. Based on our documentation, configuration differences between environments are often caused by scope overrides or hidden environment overrides.
> 
> Please try the following steps to identify the source:
> 1. Check the scope at which the variable was defined. Service scope overrides project scope, and project scope overrides organisation defaults [DOC-DEPLOY-004].
> 2. Review the environment overrides page, which lists values that differ from the defaults for each environment [DOC-DEPLOY-004].
> 3. If you make any changes to the configuration, remember to redeploy the service, as running containers do not pick up new values without a restart [DOC-DEPLOY-004].
> 
> If you find that sensitive values are being exposed in logs or are not properly masked, please ensure they are stored as secrets rather than variables, as secrets are masked in logs and not readable through the API after creation [DOC-DEPLOY-004].

**Retrieved passages:**

- **DOC-DEPLOY-004 (cited)**, Configuring environment variables and secrets: # Configuring environment variables and secrets

**Applies to:** All compute services

## Symptoms

- The application cannot read a variable that appears to be set
- A secret value appears in plain text in the logs
- Configuration differs between environments unexpectedly

## Common causes

- The variable was set at project scope but read at service scope
- The application logs its configuration at startup
- An environment override exists that is not visible on the main settings page

## Resolution

- **DOC-DEPLOY-004 (cited)**, Configuring environment variables and secrets: ## Resolution

1. Check the scope at which the variable was defined. Service scope overrides project scope, and project scope overrides organisation defaults.
2. Store anything sensitive as a secret rather than a variable. Secrets are masked in logs and are not readable through the API after creation.
3. Review the environment overrides page, which lists values that differ from the defaults for each environment.
4. Redeploy after changing configuration. Running containers do not pick up new values without a restart.

## Notes

A secret that has been printed to logs should be treated as exposed and rotated, even if the logs are private.

- **DOC-BILL-003**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

- **DOC-DEPLOY-002**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

- **DOC-SEC-002**, Handling exposed secrets and credential rotation: # Handling exposed secrets and credential rotation

**Applies to:** All plans

## Symptoms

- A key has been committed to a repository
- A secret appears in application logs
- A third party has reported finding a credential

## Common causes

- Configuration was committed rather than referenced from the environment
- The application prints its configuration during startup
- A key was shared in a support ticket or a chat message

## Resolution

---

## 27. VAL-0060

**Channel:** email | **Customer plan:** business

**Subject:** Webhooks not arriving

**Ticket body:**

> Signature verification fails for every delivery. We are computing the signature exactly as the documentation describes, over the parsed body.

**Draft reply:**

> Hi,
> 
> Thanks for reaching out. Based on your description, the issue is likely caused by computing the signature over the parsed body rather than the raw bytes [DOC-API-003]. Re-serialising JSON changes the bytes and invalidates the signature [DOC-API-003].
> 
> Please ensure you compute the signature over the raw request body before any parsing [DOC-API-003]. Additionally, verify that your endpoint returns a 2xx status as quickly as possible, as deliveries time out after five seconds [DOC-API-003]. You can check the webhook delivery log for the last seven days to review response statuses and bodies [DOC-API-003].
> 
> Let us know if this resolves the issue.
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-API-003 (cited)**, Webhook delivery, retries and signature verification: # Webhook delivery, retries and signature verification

**Applies to:** All plans

## Symptoms

- Webhooks are not arriving at the configured endpoint
- The same event is delivered more than once
- Signature verification fails

## Common causes

- The endpoint returned a non-2xx status and delivery is being retried
- The endpoint responded too slowly and the delivery timed out
- The signature was computed over a parsed body rather than the raw bytes

## Resolution

- **DOC-API-003 (cited)**, Webhook delivery, retries and signature verification: ## Resolution

1. Check the webhook delivery log, which records every attempt with the response status and body for the last seven days.
2. Return 2xx as quickly as possible and process the event asynchronously. Deliveries time out after five seconds.
3. Compute the signature over the raw request body before any parsing. Re-serialising JSON changes the bytes and invalidates the signature.
4. Make your handler idempotent using the event identifier. At-least-once delivery means duplicates are expected rather than exceptional.

## Notes

Failed deliveries are retried with backoff for twenty-four hours, after which the endpoint is disabled and the account is notified.

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: # Single sign-on configuration with SAML providers

**Applies to:** Business and Enterprise plans

## Symptoms

- Users are redirected to the identity provider and returned to an error page
- SSO works for some users and not others
- New users are not provisioned automatically

## Common causes

- The assertion consumer service URL does not match the value registered with CloudServe
- The email attribute in the assertion does not match the CloudServe account email
- Just-in-time provisioning is disabled on the connection

## Resolution

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: ## Resolution

1. Compare the assertion consumer service URL in your identity provider against the value shown on the SSO settings page. They must match exactly, including the trailing path.
2. Inspect a failing assertion and confirm the NameID is the user's email address in lower case.
3. Enable just-in-time provisioning if new users should be created on first login, and set a default role for provisioned users.
4. Keep at least one administrator account with password access while testing, so a misconfiguration does not lock the whole organisation out.

## Notes

SAML changes take effect immediately for new sessions but existing sessions remain valid until they expire.

- **DOC-INT-001**, Connecting continuous integration pipelines: # Connecting continuous integration pipelines

**Applies to:** All plans

## Symptoms

- The pipeline cannot authenticate against CloudServe
- Deployments succeed manually but fail from the pipeline
- The pipeline has broader access than intended

## Common causes

- A personal key was used rather than a service account
- The pipeline environment lacks the configuration present locally
- The service account was granted an organisation-wide role

## Resolution

---

## 28. VAL-0073

**Channel:** forum | **Customer plan:** business

**Subject:** Invoice higher than expected

**Ticket body:**

> bill is very high this month. i not understand the charge. please explain what is this.

**Draft reply:**

> Hi there, I understand that your invoice is higher than expected. To help you understand the charges, please follow these steps: 1. Open the usage breakdown for the period, which itemises charges by service and by environment [DOC-BILL-001]. 2. Look for resources in staging or development environments, which are billed at the same rate as production [DOC-BILL-001]. 3. Check the billing period dates at the top of the invoice; the period runs from the anniversary of your subscription date rather than the first of the month [DOC-BILL-001]. 4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it [DOC-BILL-001]. If you recently upgraded your plan, the charge may differ from the advertised price because upgrades are prorated for the days remaining in the period and shown as a separate line [DOC-BILL-002]. Please let me know if you need further assistance.

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002 (cited)**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002 (cited)**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-API-001**, Understanding API rate limits and quota tiers: # Understanding API rate limits and quota tiers

**Applies to:** All plans

## Symptoms

- Requests return 429 Too Many Requests
- Throughput drops sharply at a predictable point
- Limits appear lower than the documented figure

## Common causes

- The limit applies per organisation rather than per key
- Burst capacity was consumed and the sustained rate now applies
- The endpoint being called has a lower limit than the general one

## Resolution

---

## 29. VAL-0011

**Channel:** forum | **Customer plan:** standard

**Subject:** How do I revert to the previous revision

**Ticket body:**

> We shipped a release yesterday morning that has broken checkout for a portion of our customers. We need to get back to the previous version quickly. What is the fastest safe route?

**Draft reply:**

> To revert to the previous revision quickly, open the revisions page for your service and identify the last healthy revision [DOC-DEPLOY-002]. Select roll back on that revision; traffic moves within roughly thirty seconds and no rebuild takes place [DOC-DEPLOY-002]. If your release included a database migration, you must roll the migration back before the service to prevent the older code from encountering an unexpected schema [DOC-DEPLOY-002]. Note that rollback restores the container image and configuration but does not restore data [DOC-DEPLOY-002]. Finally, record the incident and the reason for the rollback before deploying a fix [DOC-DEPLOY-002].

**Retrieved passages:**

- **DOC-DEPLOY-002 (cited)**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

- **DOC-DEPLOY-002 (cited)**, Rolling back a failed release: # Rolling back a failed release

**Applies to:** Container Service, Functions

## Symptoms

- A release has introduced errors and must be reverted
- The previous revision is needed while a fix is prepared

## Common causes

- A defect reached production that testing did not catch
- A configuration change had unintended effects

## Resolution

- **DOC-DATA-002**, Backups, retention and point-in-time restore: ## Resolution

1. Identify the point you need to restore to. Point-in-time recovery covers any moment within the retention window rather than only backup times.
2. Restore into a new database instance rather than over the existing one, so the current state is preserved while you verify the restore.
3. Allow roughly ten minutes per hundred gigabytes for the restore, and considerably longer where the instance is also under load.
4. Verify the restored data before switching traffic, and keep the original instance until that verification is complete.

## Notes

Retention is seven days on Standard, thirty days on Business and ninety days on Enterprise plans.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

---

## 30. VAL-0075

**Channel:** docs_comment | **Customer plan:** business

**Subject:** API key returning 401

**Ticket body:**

> A key can read fine but every write returns a permission error. I created it myself and I thought I gave it full access.

**Draft reply:**

> Hi there, thanks for reaching out. A 401 error on write requests while reads succeed usually points to a scope mismatch. Please check the API keys page to review the scopes attached to your key. Read-only keys cannot perform write operations, and project-scoped keys cannot reach organisation endpoints [DOC-AUTH-004]. If the key is missing the necessary write permissions, you may need to create a new key with the appropriate scopes. To do this without downtime, create the replacement key first, deploy it, confirm traffic has moved, and then revoke the old key [DOC-AUTH-004]. Let us know if you need further assistance.

**Retrieved passages:**

- **DOC-AUTH-004 (cited)**, API key rotation and scope management: # API key rotation and scope management

**Applies to:** All plans

## Symptoms

- A previously working key returns 401 Unauthorized
- A key works for some endpoints and not others
- A key needs replacing after accidental exposure

## Common causes

- The key was revoked or reached its configured expiry
- The key was issued with a scope that excludes the endpoint being called
- The key belongs to a deleted user and was removed with the account

## Resolution

- **DOC-AUTH-004 (cited)**, API key rotation and scope management: ## Resolution

1. Check the API keys page for the key's status and expiry. Revoked and expired keys are listed with the date and the user who acted.
2. Review the scopes attached to the key. Read-only keys cannot write, and project-scoped keys cannot reach organisation endpoints.
3. To rotate without downtime, create the replacement key first, deploy it, confirm traffic has moved, then revoke the old key.
4. If a key has been exposed publicly, revoke it immediately rather than waiting for the rotation window.

## Notes

Keys issued to individual users are removed when that user is deleted. Use service accounts for anything running in production.

- **DOC-API-001**, Understanding API rate limits and quota tiers: # Understanding API rate limits and quota tiers

**Applies to:** All plans

## Symptoms

- Requests return 429 Too Many Requests
- Throughput drops sharply at a predictable point
- Limits appear lower than the documented figure

## Common causes

- The limit applies per organisation rather than per key
- Burst capacity was consumed and the sustained rate now applies
- The endpoint being called has a lower limit than the general one

## Resolution

- **DOC-INT-001**, Connecting continuous integration pipelines: ## Resolution

1. Create a service account for the pipeline rather than using a personal key, so that access survives staff changes.
2. Grant the service account only the projects and permissions the pipeline needs, and review that grant when the pipeline changes.
3. Store the credential as an encrypted secret in your pipeline provider, never in the repository.
4. Test the pipeline credential separately from the deployment logic, so that authentication failures are distinguishable from deployment failures.

## Notes

Service account keys do not expire by default. Set an expiry and rotate on a schedule.

- **DOC-ACCT-001**, Managing team members, roles and permissions: ## Resolution

1. Check the effective permissions view for the user, which resolves direct roles and group memberships together.
2. Confirm the invitation was accepted. Pending invitations appear in a separate section and expire after seven days.
3. Remove a departing user rather than only changing their password, and revoke any API keys they created.
4. Prefer group membership to direct role assignment, so that access can be reviewed in one place.

## Notes

Removing the last account owner is not permitted. Transfer ownership before removing the account.

---

## 31. VAL-0022

**Channel:** docs_comment | **Customer plan:** standard

**Subject:** Service slow at peak hours

**Ticket body:**

> The service is noticeably slow during our afternoon peak and fine the rest of the day. We have autoscaling enabled so I expected it to cope.

**Draft reply:**

> Hi, thanks for flagging the latency issues during your afternoon peak. Since you have autoscaling enabled, the delay may be caused by the scaling metric reacting slower than the load changes, or the service hitting its configured maximum instance count [DOC-PERF-002]. Additionally, if the scaling events are frequent, cold starts on new instances can raise the 95th percentile latency even if the service itself is healthy [DOC-PERF-001]. To diagnose this, please compare the median and 95th percentile latency on the metrics page to check for queueing or contention [DOC-PERF-001]. You should also review the dependency timing breakdown to see if the delay is coming from your service or a downstream dependency [DOC-PERF-001]. For autoscaling adjustments, consider scaling on request concurrency rather than processor utilisation, as it reacts faster for request-bound services [DOC-PERF-002]. Also, ensure your cooldown period is longer than your instance startup time to prevent oscillation, and consider setting a minimum instance count above zero to avoid cold starts [DOC-PERF-002].

**Retrieved passages:**

- **DOC-PERF-001 (cited)**, Diagnosing elevated response latency: ## Resolution

1. Compare median and 95th percentile latency on the metrics page. A large gap points to contention or queueing rather than a uniformly slower service.
2. Check memory utilisation across instances. Sustained utilisation above eighty per cent typically shows up as latency before it shows up as failure.
3. Review the dependency timing breakdown on the trace view to identify whether the time is being spent in your service or waiting on another.
4. Adjust the autoscaling policy if load is predictable. Scaling on request count responds sooner than scaling on processor utilisation.

## Notes

Cold starts affect the first request to a new instance. Frequent scaling events will therefore raise the 95th percentile even when the service itself is healthy.

- **DOC-PERF-001 (cited)**, Diagnosing elevated response latency: # Diagnosing elevated response latency

**Applies to:** All compute services

## Symptoms

- Response times have increased without a code change
- The 95th percentile is far above the median
- Latency rises at predictable times of day

## Common causes

- The service is running close to its memory limit and spending time in garbage collection
- A downstream dependency has slowed and the delay is propagating
- Instance count is not scaling with the load pattern

## Resolution

- **DOC-PERF-002 (cited)**, Autoscaling behaviour and instance limits: ## Resolution

1. Check whether the service is sitting at its configured maximum. Scaling stops there regardless of load.
2. Choose a scaling metric that reflects the pressure you actually face. Request concurrency reacts faster than processor utilisation for request-bound services.
3. Set the cooldown longer than your startup time so that new instances are counted before another scaling decision is taken.
4. Set a minimum instance count above zero for latency-sensitive services to avoid cold starts on the first request.

## Notes

Scaling decisions are evaluated every fifteen seconds. Very short traffic spikes will finish before scaling responds.

- **DOC-PERF-002 (cited)**, Autoscaling behaviour and instance limits: # Autoscaling behaviour and instance limits

**Applies to:** Container Service

## Symptoms

- The service does not scale up under load
- Scaling happens later than expected
- Instance count oscillates

## Common causes

- The maximum instance count has been reached
- The scaling metric responds more slowly than the load changes
- The cooldown period is shorter than the time a new instance takes to become ready

## Resolution

- **DOC-API-001**, Understanding API rate limits and quota tiers: # Understanding API rate limits and quota tiers

**Applies to:** All plans

## Symptoms

- Requests return 429 Too Many Requests
- Throughput drops sharply at a predictable point
- Limits appear lower than the documented figure

## Common causes

- The limit applies per organisation rather than per key
- Burst capacity was consumed and the sustained rate now applies
- The endpoint being called has a lower limit than the general one

## Resolution

---

## 32. VAL-0080

**Channel:** chat | **Customer plan:** standard

**Subject:** 

**Ticket body:**

> Builds that worked last week are now failing during dependency resolution. We have not changed our code at all. This is blocking a release we had planned for yesterday morning.

**Draft reply:**

> I understand that builds which previously succeeded are now failing during dependency resolution without any code changes, and that this is blocking a release. Based on our documentation, this is a known issue often caused by unpinned dependencies, runtime mismatches, or corrupted cache artifacts [DOC-DEPLOY-003]. To resolve this, please try the following steps:
> 
> 1. Pin your dependencies with exact versions and commit the lock file, as unpinned dependencies are the most common cause [DOC-DEPLOY-003].
> 2. Compare the runtime version declared in your build configuration against the version you use locally [DOC-DEPLOY-003].
> 3. Clear the build cache from the settings page and trigger a fresh build to rule out a corrupted artifact [DOC-DEPLOY-003].
> 4. If a specific dependency is failing, check whether its registry is reachable from the build network [DOC-DEPLOY-003].
> 
> Additionally, build logs retain the full resolution output for thirty days, which should help identify which version changed [DOC-DEPLOY-003].

**Retrieved passages:**

- **DOC-DEPLOY-003 (cited)**, Build failures caused by dependency resolution: # Build failures caused by dependency resolution

**Applies to:** Build Service

## Symptoms

- Builds that previously succeeded now fail without code changes
- The build works locally but fails in the pipeline
- Dependency resolution takes far longer than usual

## Common causes

- An unpinned dependency released a new incompatible version
- The build environment uses a different language runtime than the local machine
- The dependency cache holds a partially written artefact

## Resolution

- **DOC-DEPLOY-003 (cited)**, Build failures caused by dependency resolution: ## Resolution

1. Pin your dependencies with exact versions and commit the lock file. Unpinned dependencies are the cause in the large majority of cases of this kind.
2. Compare the runtime version declared in your build configuration against the version you use locally.
3. Clear the build cache from the settings page and trigger a fresh build to rule out a corrupted artefact.
4. If a specific dependency is failing to resolve, check whether its registry is reachable from the build network.

## Notes

Build logs retain the full resolution output for thirty days, which is usually enough to identify which version changed.

- **DOC-ONB-001**, First deployment: a walkthrough: # First deployment: a walkthrough

**Applies to:** All plans

## Symptoms

- A new user does not know where to begin
- The first deployment fails for unclear reasons

## Common causes

- Required configuration has not been set
- The project structure does not match what the build expects

## Resolution

1. Create a project, then a service within it. Resources belong to services and services belong to projects.
2. Connect a repository or push a container image. The build service detects common project layouts automatically.
3. Set any environment variables the application needs before the first deployment rather than after it.
4. Deploy, then watch the logs for the first sixty seconds. Most first-deployment problems are visible immediately in startup output.

## Notes

- **DOC-DEPLOY-002**, Rolling back a failed release: # Rolling back a failed release

**Applies to:** Container Service, Functions

## Symptoms

- A release has introduced errors and must be reverted
- The previous revision is needed while a fix is prepared

## Common causes

- A defect reached production that testing did not catch
- A configuration change had unintended effects

## Resolution

- **DOC-DEPLOY-001**, Container deployments failing during the health check phase: ## Resolution

1. Confirm the container is listening on the port declared in the service definition. A mismatch here produces a health check failure that looks like a timeout.
2. Increase the initial delay if the application needs time to warm up before it can answer. Thirty seconds is a reasonable starting point for services that load models or caches.
3. Compare the environment variables present in the deployment against those the application requires. Missing configuration frequently causes a silent startup failure.
4. Inspect the container logs from the failed revision rather than the running one; the rollback replaces the logs shown by default.

## Notes

---

## 33. VAL-0016

**Channel:** chat | **Customer plan:** standard

**Subject:** 

**Ticket body:**

> The service is noticeably slow during our afternoon peak and fine the rest of the day. We have autoscaling enabled so I expected it to cope.

**Draft reply:**

> Hi, I understand the service is experiencing latency during afternoon peaks despite autoscaling being enabled. This pattern often occurs when the scaling metric reacts slower than the load changes or when the service hits its configured maximum instance count [DOC-PERF-002]. Additionally, if the scaling cooldown is shorter than the instance startup time, new instances may not be counted before the next scaling decision, leading to oscillation or delayed response [DOC-PERF-002].
> 
> To diagnose this, please check if the service is sitting at its configured maximum instance count [DOC-PERF-002]. You should also review your scaling metric; for request-bound services, scaling on request concurrency or count typically responds sooner than processor utilisation [DOC-PERF-001, DOC-PERF-002]. Finally, ensure your cooldown period is set longer than your instance startup time to prevent premature scaling decisions [DOC-PERF-002].

**Retrieved passages:**

- **DOC-PERF-001**, Diagnosing elevated response latency: ## Resolution

1. Compare median and 95th percentile latency on the metrics page. A large gap points to contention or queueing rather than a uniformly slower service.
2. Check memory utilisation across instances. Sustained utilisation above eighty per cent typically shows up as latency before it shows up as failure.
3. Review the dependency timing breakdown on the trace view to identify whether the time is being spent in your service or waiting on another.
4. Adjust the autoscaling policy if load is predictable. Scaling on request count responds sooner than scaling on processor utilisation.

## Notes

Cold starts affect the first request to a new instance. Frequent scaling events will therefore raise the 95th percentile even when the service itself is healthy.

- **DOC-PERF-001**, Diagnosing elevated response latency: # Diagnosing elevated response latency

**Applies to:** All compute services

## Symptoms

- Response times have increased without a code change
- The 95th percentile is far above the median
- Latency rises at predictable times of day

## Common causes

- The service is running close to its memory limit and spending time in garbage collection
- A downstream dependency has slowed and the delay is propagating
- Instance count is not scaling with the load pattern

## Resolution

- **DOC-PERF-002 (cited)**, Autoscaling behaviour and instance limits: ## Resolution

1. Check whether the service is sitting at its configured maximum. Scaling stops there regardless of load.
2. Choose a scaling metric that reflects the pressure you actually face. Request concurrency reacts faster than processor utilisation for request-bound services.
3. Set the cooldown longer than your startup time so that new instances are counted before another scaling decision is taken.
4. Set a minimum instance count above zero for latency-sensitive services to avoid cold starts on the first request.

## Notes

Scaling decisions are evaluated every fifteen seconds. Very short traffic spikes will finish before scaling responds.

- **DOC-PERF-002 (cited)**, Autoscaling behaviour and instance limits: # Autoscaling behaviour and instance limits

**Applies to:** Container Service

## Symptoms

- The service does not scale up under load
- Scaling happens later than expected
- Instance count oscillates

## Common causes

- The maximum instance count has been reached
- The scaling metric responds more slowly than the load changes
- The cooldown period is shorter than the time a new instance takes to become ready

## Resolution

- **DOC-API-001**, Understanding API rate limits and quota tiers: # Understanding API rate limits and quota tiers

**Applies to:** All plans

## Symptoms

- Requests return 429 Too Many Requests
- Throughput drops sharply at a predictable point
- Limits appear lower than the documented figure

## Common causes

- The limit applies per organisation rather than per key
- Burst capacity was consumed and the sustained rate now applies
- The endpoint being called has a lower limit than the general one

## Resolution

---

## 34. VAL-0004

**Channel:** email | **Customer plan:** business

**Subject:** MFA code keeps getting rejected

**Ticket body:**

> my authenticator app codes are being rejected every time. i am having tried generating new ones several times.

**Draft reply:**

> Hi there,
> 
> I understand that your authenticator app codes are being rejected. The most common cause for this is a device clock drift of more than thirty seconds, which invalidates time-based codes [DOC-AUTH-002]. Please check that automatic time synchronisation is enabled on the device generating the code [DOC-AUTH-002].
> 
> If the issue persists, please confirm that the authenticator was not enrolled against a different account [DOC-AUTH-002]. Additionally, if you have regenerated your recovery codes previously, this would have invalidated any older set of codes [DOC-AUTH-002].
> 
> If you are unable to resolve this by checking your device time, please let us know if you have access to any valid recovery codes or if you require an administrator to reset your multi-factor authentication [DOC-AUTH-002].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-AUTH-002 (cited)**, Multi-factor authentication setup and recovery: # Multi-factor authentication setup and recovery

**Applies to:** All plans

## Symptoms

- The authenticator code is rejected as invalid
- A user has lost the device holding their authenticator
- Recovery codes were never downloaded

## Common causes

- Device clock drift of more than thirty seconds invalidates time-based codes
- The authenticator was enrolled against a different account
- Recovery codes were regenerated, invalidating the older set

## Resolution

- **DOC-AUTH-002 (cited)**, Multi-factor authentication setup and recovery: ## Resolution

1. Ask the user to check that automatic time synchronisation is enabled on the device generating the code. Drift is the most common cause by a wide margin.
2. If the device is lost, the user should sign in with one of their recovery codes and then re-enrol a new device from the security page.
3. Where no recovery codes are available, an account administrator can reset multi-factor authentication for that user from the team members page.
4. If the user is the sole administrator and has no recovery codes, identity verification through support is required and takes up to one business day.

## Notes

Support cannot disable multi-factor authentication without identity verification, regardless of urgency.

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: ## Resolution

1. Compare the assertion consumer service URL in your identity provider against the value shown on the SSO settings page. They must match exactly, including the trailing path.
2. Inspect a failing assertion and confirm the NameID is the user's email address in lower case.
3. Enable just-in-time provisioning if new users should be created on first login, and set a default role for provisioned users.
4. Keep at least one administrator account with password access while testing, so a misconfiguration does not lock the whole organisation out.

## Notes

SAML changes take effect immediately for new sessions but existing sessions remain valid until they expire.

- **DOC-AUTH-003**, Single sign-on configuration with SAML providers: # Single sign-on configuration with SAML providers

**Applies to:** Business and Enterprise plans

## Symptoms

- Users are redirected to the identity provider and returned to an error page
- SSO works for some users and not others
- New users are not provisioned automatically

## Common causes

- The assertion consumer service URL does not match the value registered with CloudServe
- The email attribute in the assertion does not match the CloudServe account email
- Just-in-time provisioning is disabled on the connection

## Resolution

- **DOC-AUTH-001**, Resolving invalid credential errors on login: # Resolving invalid credential errors on login

**Applies to:** Console, CLI, SDK

## Symptoms

- The console returns 'Invalid credentials' despite a correct password
- Login succeeds in one browser but fails in another
- The CLI reports authentication failure after a working period

## Common causes

- The account is locked after five consecutive failed attempts
- A stale session cookie is being sent alongside new credentials
- The password was changed in another session and the client cached the old one

## Resolution

---

## 35. VAL-0028

**Channel:** email | **Customer plan:** business

**Subject:** Deployment rolls back every time

**Ticket body:**

> builds that work last week are now fail during dependency resolution. we having not change our code at all.

**Draft reply:**

> Hi there,
> 
> I understand that your builds are failing during dependency resolution despite no code changes, causing deployments to roll back. This is a known issue often caused by unpinned dependencies or environment mismatches.
> 
> To resolve this, please try the following steps:
> 1. Pin your dependencies with exact versions and commit the lock file, as unpinned dependencies are the most common cause of this issue [DOC-DEPLOY-003].
> 2. Compare the runtime version declared in your build configuration against the version you use locally to ensure they match [DOC-DEPLOY-003].
> 3. Clear the build cache from the settings page and trigger a fresh build to rule out a corrupted artefact [DOC-DEPLOY-003].
> 4. If a specific dependency is failing, check whether its registry is reachable from the build network [DOC-DEPLOY-003].
> 
> Additionally, build logs retain the full resolution output for thirty days, which can help identify which version changed [DOC-DEPLOY-003].
> 
> If you need to revert to a previous stable state while investigating, you can roll back to the last healthy revision from the revisions page; traffic moves within roughly thirty seconds and no rebuild takes place [DOC-DEPLOY-002]. Note that if the release included a database migration, you must roll the migration back before the service [DOC-DEPLOY-002].
> 
> Let us know if you need further assistance.

**Retrieved passages:**

- **DOC-DEPLOY-003 (cited)**, Build failures caused by dependency resolution: # Build failures caused by dependency resolution

**Applies to:** Build Service

## Symptoms

- Builds that previously succeeded now fail without code changes
- The build works locally but fails in the pipeline
- Dependency resolution takes far longer than usual

## Common causes

- An unpinned dependency released a new incompatible version
- The build environment uses a different language runtime than the local machine
- The dependency cache holds a partially written artefact

## Resolution

- **DOC-DEPLOY-003 (cited)**, Build failures caused by dependency resolution: ## Resolution

1. Pin your dependencies with exact versions and commit the lock file. Unpinned dependencies are the cause in the large majority of cases of this kind.
2. Compare the runtime version declared in your build configuration against the version you use locally.
3. Clear the build cache from the settings page and trigger a fresh build to rule out a corrupted artefact.
4. If a specific dependency is failing to resolve, check whether its registry is reachable from the build network.

## Notes

Build logs retain the full resolution output for thirty days, which is usually enough to identify which version changed.

- **DOC-ONB-001**, First deployment: a walkthrough: # First deployment: a walkthrough

**Applies to:** All plans

## Symptoms

- A new user does not know where to begin
- The first deployment fails for unclear reasons

## Common causes

- Required configuration has not been set
- The project structure does not match what the build expects

## Resolution

1. Create a project, then a service within it. Resources belong to services and services belong to projects.
2. Connect a repository or push a container image. The build service detects common project layouts automatically.
3. Set any environment variables the application needs before the first deployment rather than after it.
4. Deploy, then watch the logs for the first sixty seconds. Most first-deployment problems are visible immediately in startup output.

## Notes

- **DOC-DEPLOY-002 (cited)**, Rolling back a failed release: # Rolling back a failed release

**Applies to:** Container Service, Functions

## Symptoms

- A release has introduced errors and must be reverted
- The previous revision is needed while a fix is prepared

## Common causes

- A defect reached production that testing did not catch
- A configuration change had unintended effects

## Resolution

- **DOC-DEPLOY-002 (cited)**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

---

## 36. VAL-0053

**Channel:** chat | **Customer plan:** enterprise

**Subject:** 

**Ticket body:**

> There are charges on our invoice for a service I do not believe we use. Could you explain what these relate to?

**Draft reply:**

> I can help you understand those charges. To identify what they relate to, please open the usage breakdown for the billing period, which itemises charges by service and by environment [DOC-BILL-001]. Look for resources in staging or development environments, as these are billed at the same rate as production [DOC-BILL-001]. Also, check the billing period dates at the top of the invoice, as the period runs from the anniversary of the subscription date rather than the calendar month [DOC-BILL-001]. If you would like to prevent unexpected charges in the future, you can set a usage alert on the billing page [DOC-BILL-001].

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-BILL-003**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

---

## 37. VAL-0057

**Channel:** email | **Customer plan:** standard

**Subject:** Deployment rolls back every time

**Ticket body:**

> Our deployment reaches running and then rolls back after about a minute. The logs mention a health check timeout. It runs perfectly on my machine and in staging.

**Draft reply:**

> Hi there,
> 
> I understand your deployment is reaching the running state but rolling back after about a minute due to health check timeouts. This is a common issue where the service works locally or in staging but fails in the production environment.
> 
> Based on the symptoms, here are the most likely causes and steps to resolve this:
> 
> 1. **Port Mismatch:** Confirm that your container is listening on the exact port declared in your service definition. A mismatch here often produces a health check failure that looks like a timeout [DOC-DEPLOY-001].
> 2. **Startup Time:** If your application needs time to warm up (e.g., loading models or caches), increase the initial delay for the health check. Thirty seconds is a reasonable starting point for such services [DOC-DEPLOY-001].
> 3. **Environment Variables:** Compare the environment variables present in your deployment against those your application requires. Missing configuration frequently causes a silent startup failure [DOC-DEPLOY-001].
> 4. **Log Inspection:** Please inspect the container logs from the *failed* revision rather than the running one, as the rollback replaces the logs shown by default [DOC-DEPLOY-001].
> 
> Additionally, ensure your health check endpoint returns within the timeout using only local state. Endpoints that call a database can fail during a database incident and take the service down with them [DOC-DEPLOY-001].
> 
> Let me know if you need further assistance after checking these items.

**Retrieved passages:**

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: # Container deployments failing during the health check phase

**Applies to:** Container Service

## Symptoms

- The deployment reaches running and then rolls back
- Logs show repeated health check timeouts
- The service works locally but not when deployed

## Common causes

- The health endpoint takes longer to respond than the configured timeout
- The container listens on a different port than the service declares
- A required environment variable is absent in the deployed environment

## Resolution

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: ## Resolution

1. Confirm the container is listening on the port declared in the service definition. A mismatch here produces a health check failure that looks like a timeout.
2. Increase the initial delay if the application needs time to warm up before it can answer. Thirty seconds is a reasonable starting point for services that load models or caches.
3. Compare the environment variables present in the deployment against those the application requires. Missing configuration frequently causes a silent startup failure.
4. Inspect the container logs from the failed revision rather than the running one; the rollback replaces the logs shown by default.

## Notes

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: ## Notes

A health check must return within the timeout using only local state. Endpoints that call a database will fail during a database incident and take the service down with them.

- **DOC-ONB-001**, First deployment: a walkthrough: # First deployment: a walkthrough

**Applies to:** All plans

## Symptoms

- A new user does not know where to begin
- The first deployment fails for unclear reasons

## Common causes

- Required configuration has not been set
- The project structure does not match what the build expects

## Resolution

1. Create a project, then a service within it. Resources belong to services and services belong to projects.
2. Connect a repository or push a container image. The build service detects common project layouts automatically.
3. Set any environment variables the application needs before the first deployment rather than after it.
4. Deploy, then watch the logs for the first sixty seconds. Most first-deployment problems are visible immediately in startup output.

## Notes

- **DOC-DEPLOY-002**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

---

## 38. VAL-0070

**Channel:** docs_comment | **Customer plan:** business

**Subject:** SSO works for some users only

**Ticket body:**

> Single sign-on works for our engineering group but the finance group gets an error. Both are configured identically as far as we can tell. Any idea what differs?

**Draft reply:**

> Hi there, 
> 
> When SSO works for some users but not others, the issue is often related to how the identity provider is configured or how user attributes are mapped. Based on our documentation, here are a few things to check:
> 
> 1. Ensure the assertion consumer service URL in your identity provider matches the value shown on the SSO settings page exactly, including the trailing path [DOC-AUTH-003].
> 2. Inspect a failing assertion to confirm the NameID is the user's email address in lower case [DOC-AUTH-003].
> 3. Verify that the email attribute in the assertion matches the CloudServe account email for the affected users [DOC-AUTH-003].
> 4. If new users should be created on first login, make sure just-in-time provisioning is enabled and a default role is set for provisioned users [DOC-AUTH-003].
> 
> Please let us know if you need further assistance or if the issue persists after checking these items. 
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-AUTH-003 (cited)**, Single sign-on configuration with SAML providers: ## Resolution

1. Compare the assertion consumer service URL in your identity provider against the value shown on the SSO settings page. They must match exactly, including the trailing path.
2. Inspect a failing assertion and confirm the NameID is the user's email address in lower case.
3. Enable just-in-time provisioning if new users should be created on first login, and set a default role for provisioned users.
4. Keep at least one administrator account with password access while testing, so a misconfiguration does not lock the whole organisation out.

## Notes

SAML changes take effect immediately for new sessions but existing sessions remain valid until they expire.

- **DOC-AUTH-003 (cited)**, Single sign-on configuration with SAML providers: # Single sign-on configuration with SAML providers

**Applies to:** Business and Enterprise plans

## Symptoms

- Users are redirected to the identity provider and returned to an error page
- SSO works for some users and not others
- New users are not provisioned automatically

## Common causes

- The assertion consumer service URL does not match the value registered with CloudServe
- The email attribute in the assertion does not match the CloudServe account email
- Just-in-time provisioning is disabled on the connection

## Resolution

- **DOC-AUTH-002**, Multi-factor authentication setup and recovery: # Multi-factor authentication setup and recovery

**Applies to:** All plans

## Symptoms

- The authenticator code is rejected as invalid
- A user has lost the device holding their authenticator
- Recovery codes were never downloaded

## Common causes

- Device clock drift of more than thirty seconds invalidates time-based codes
- The authenticator was enrolled against a different account
- Recovery codes were regenerated, invalidating the older set

## Resolution

- **DOC-AUTH-002**, Multi-factor authentication setup and recovery: ## Resolution

1. Ask the user to check that automatic time synchronisation is enabled on the device generating the code. Drift is the most common cause by a wide margin.
2. If the device is lost, the user should sign in with one of their recovery codes and then re-enrol a new device from the security page.
3. Where no recovery codes are available, an account administrator can reset multi-factor authentication for that user from the team members page.
4. If the user is the sole administrator and has no recovery codes, identity verification through support is required and takes up to one business day.

## Notes

Support cannot disable multi-factor authentication without identity verification, regardless of urgency.

- **DOC-SEC-001**, Responding to a suspected account compromise: # Responding to a suspected account compromise

**Applies to:** All plans

## Symptoms

- Unrecognised activity appears in the audit log
- A user reports credentials may have been exposed
- Resources were created that nobody claims

## Common causes

- Credentials were reused from a service that suffered a breach
- An API key was committed to a public repository
- A former team member retained access after leaving

## Resolution

---

## 39. VAL-0064

**Channel:** chat | **Customer plan:** business

**Subject:** 

**Ticket body:**

> What is the right way to pull a very large extract? Requesting a big page size gets rejected and iterating page by page takes hours.

**Draft reply:**

> For very large extracts, the recommended approach is to use the export endpoint, which runs asynchronously and returns a download link [DOC-API-002]. This avoids the need to iterate through pages manually. If you do need to use pagination for other queries, keep the page size at or below 200, as larger requests are rejected [DOC-API-002]. Additionally, use cursor pagination rather than offset pagination to prevent skipping or repeating records if the data changes during iteration [DOC-API-002]. Note that export jobs covering more than a million records can take several minutes to complete [DOC-DATA-001].

**Retrieved passages:**

- **DOC-API-002 (cited)**, Pagination and handling large result sets: ## Resolution

1. Use cursor pagination for anything that may change while you iterate. Offset pagination will skip or repeat records when items are inserted mid-iteration.
2. Pass the next_cursor value from each response as the cursor parameter of the following request, and stop when it is null.
3. Keep page size at or below two hundred. Larger requests are rejected rather than truncated.
4. For very large extracts, use the export endpoint, which runs asynchronously and returns a download link.

## Notes

Cursors expire after one hour. Long-running iterations should handle expiry by restarting from a recorded checkpoint.

- **DOC-API-002 (cited)**, Pagination and handling large result sets: # Pagination and handling large result sets

**Applies to:** All plans

## Symptoms

- Only the first page of results is returned
- Iterating through results misses or duplicates records
- Large queries time out

## Common causes

- The cursor from the previous response was not passed to the next request
- Offset pagination was used against a changing collection
- The page size requested exceeds the maximum

## Resolution

- **DOC-API-001**, Understanding API rate limits and quota tiers: ## Resolution

1. Read the rate limit headers returned with every response. They give the limit, the remaining allowance and the reset time, which is more reliable than inferring the limit from behaviour.
2. Confirm whether the endpoint has a specific limit. Search and export endpoints are more expensive and are limited more tightly than reads.
3. Implement exponential backoff with jitter on 429 responses rather than retrying immediately, which prolongs the throttling.
4. Where sustained higher throughput is genuinely required, the limit can be raised on Business and Enterprise plans through an account request.

## Notes

Limits are enforced per organisation. Issuing more keys does not increase the available quota.

- **DOC-DATA-001 (cited)**, Exporting account data and scheduled extracts: # Exporting account data and scheduled extracts

**Applies to:** All plans

## Symptoms

- An export has not completed
- The download link has expired
- The export is missing recent records

## Common causes

- Large exports are queued and processed asynchronously
- Download links are valid for twenty-four hours
- The export captured a snapshot taken when the job started

## Resolution

- **DOC-DATA-001 (cited)**, Exporting account data and scheduled extracts: ## Resolution

1. Check the exports page for job status. Jobs covering more than a million records commonly take several minutes.
2. Request a fresh link from the exports page if the original has expired. The underlying file is retained for seven days.
3. Note that the export reflects the moment the job began, so records created during processing are not included.
4. For recurring needs, configure a scheduled export delivered to object storage rather than generating them manually.

## Notes

Exports containing personal data are logged in the audit trail with the requesting user and the fields included.

---

## 40. VAL-0050

**Channel:** email | **Customer plan:** enterprise

**Subject:** Getting started with first deployment

**Ticket body:**

> We have just signed up and I am not sure where to start. We have a containerised application and would like to get it deployed.

**Draft reply:**

> Hi there,
> 
> Welcome to the platform. Since you have a containerised application, here are the steps to get your first deployment running:
> 
> 1. Create a project, then create a service within it, as resources belong to services and services belong to projects [DOC-ONB-001].
> 2. Push your container image to connect it to the service [DOC-ONB-001].
> 3. Set any environment variables your application needs before the first deployment [DOC-ONB-001].
> 4. Deploy the service and watch the logs for the first sixty seconds, as most first-deployment problems are visible immediately in the startup output [DOC-ONB-001].
> 
> If the deployment fails during the health check phase, ensure the container is listening on the port declared in the service definition and that all required environment variables are present [DOC-DEPLOY-001].
> 
> Let us know if you run into any specific issues during this process.
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-ONB-001 (cited)**, First deployment: a walkthrough: # First deployment: a walkthrough

**Applies to:** All plans

## Symptoms

- A new user does not know where to begin
- The first deployment fails for unclear reasons

## Common causes

- Required configuration has not been set
- The project structure does not match what the build expects

## Resolution

1. Create a project, then a service within it. Resources belong to services and services belong to projects.
2. Connect a repository or push a container image. The build service detects common project layouts automatically.
3. Set any environment variables the application needs before the first deployment rather than after it.
4. Deploy, then watch the logs for the first sixty seconds. Most first-deployment problems are visible immediately in startup output.

## Notes

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: ## Resolution

1. Confirm the container is listening on the port declared in the service definition. A mismatch here produces a health check failure that looks like a timeout.
2. Increase the initial delay if the application needs time to warm up before it can answer. Thirty seconds is a reasonable starting point for services that load models or caches.
3. Compare the environment variables present in the deployment against those the application requires. Missing configuration frequently causes a silent startup failure.
4. Inspect the container logs from the failed revision rather than the running one; the rollback replaces the logs shown by default.

## Notes

- **DOC-ONB-002**, Migrating an existing application to CloudServe: ## Resolution

1. Externalise configuration before migrating. Anything read from a file on disk should move to environment variables or secrets.
2. Identify local state such as uploaded files or session data and move it to object storage or the managed database first.
3. Run in parallel with the existing deployment and shift a small share of traffic before committing to the move.
4. Plan the database migration separately from the application migration; attempting both at once makes any failure hard to diagnose.

## Notes

Applications that write to the local filesystem will lose that data on every deployment and every scaling event.

- **DOC-ONB-002**, Migrating an existing application to CloudServe: # Migrating an existing application to CloudServe

**Applies to:** All plans

## Symptoms

- An existing application needs moving with minimal downtime
- The application depends on services not yet available

## Common causes

- Configuration is embedded in the application rather than externalised
- The application depends on local state that will not survive scaling

## Resolution

- **DOC-DEPLOY-001 (cited)**, Container deployments failing during the health check phase: # Container deployments failing during the health check phase

**Applies to:** Container Service

## Symptoms

- The deployment reaches running and then rolls back
- Logs show repeated health check timeouts
- The service works locally but not when deployed

## Common causes

- The health endpoint takes longer to respond than the configured timeout
- The container listens on a different port than the service declares
- A required environment variable is absent in the deployed environment

## Resolution

---

## 41. VAL-0063

**Channel:** email | **Customer plan:** business

**Subject:** Permission changes not taking effect

**Ticket body:**

> One of our developers cannot see a project she should have access to. I have granted her the role twice and it does not seem to take effect.

**Draft reply:**

> Hi there,
> 
> Thanks for reaching out. Since granting the role twice has not resolved the issue, please check the following:
> 
> 1. Verify the scope of the role: Ensure the role was granted at the organisation scope rather than just the project scope, as project-scope roles may not grant access to the specific project in question [DOC-ACCT-001].
> 2. Check the effective permissions view: This view resolves direct roles and group memberships together to show the actual access level [DOC-ACCT-001].
> 3. Confirm invitation status: If the user was invited rather than already existing, ensure the invitation was accepted. Pending invitations expire after seven days [DOC-ACCT-001].
> 4. Review group memberships: A group membership might be granting broader or conflicting access than the direct role suggests [DOC-ACCT-001].
> 
> Please let us know if these steps resolve the issue or if you need further assistance.

**Retrieved passages:**

- **DOC-ACCT-001 (cited)**, Managing team members, roles and permissions: # Managing team members, roles and permissions

**Applies to:** All plans

## Symptoms

- A user cannot access a project they should be able to
- A departing user needs removing
- Permissions need narrowing after a review

## Common causes

- The role was granted at project scope rather than organisation scope
- The invitation was never accepted and the account does not exist
- A group membership grants broader access than the direct role suggests

## Resolution

- **DOC-SEC-002**, Handling exposed secrets and credential rotation: ## Resolution

1. Revoke the exposed credential first. Removing it from the repository does not help, because it remains in the history.
2. Issue a replacement with the narrowest scope that still works, rather than recreating the original permissions by default.
3. Search the audit log for use of the exposed credential from unfamiliar addresses during the exposure window.
4. Add secret scanning to your pipeline so that the next occurrence is caught before it reaches a remote branch.

## Notes

Never send a live credential to support. Support will never ask for one, and any credential shared in a ticket must be treated as exposed.

- **DOC-SEC-001**, Responding to a suspected account compromise: ## Resolution

1. Revoke all API keys for the affected account immediately. This is disruptive and it is the correct first action.
2. Force a password reset and terminate active sessions for the affected users from the team members page.
3. Review the audit log for the period in question, filtering by the affected user, and record anything unexpected before it ages out.
4. Enable multi-factor authentication for all users if it is not already mandatory for the organisation.

## Notes

Audit logs are retained for ninety days on Business plans and one year on Enterprise. Export them promptly during an investigation.

- **DOC-ACCT-001 (cited)**, Managing team members, roles and permissions: ## Resolution

1. Check the effective permissions view for the user, which resolves direct roles and group memberships together.
2. Confirm the invitation was accepted. Pending invitations appear in a separate section and expire after seven days.
3. Remove a departing user rather than only changing their password, and revoke any API keys they created.
4. Prefer group membership to direct role assignment, so that access can be reviewed in one place.

## Notes

Removing the last account owner is not permitted. Transfer ownership before removing the account.

- **DOC-AUTH-002**, Multi-factor authentication setup and recovery: ## Resolution

1. Ask the user to check that automatic time synchronisation is enabled on the device generating the code. Drift is the most common cause by a wide margin.
2. If the device is lost, the user should sign in with one of their recovery codes and then re-enrol a new device from the security page.
3. Where no recovery codes are available, an account administrator can reset multi-factor authentication for that user from the team members page.
4. If the user is the sole administrator and has no recovery codes, identity verification through support is required and takes up to one business day.

## Notes

Support cannot disable multi-factor authentication without identity verification, regardless of urgency.

---

## 42. VAL-0069

**Channel:** chat | **Customer plan:** business

**Subject:** 

**Ticket body:**

> Our staging environment is picking up production configuration values. I cannot work out where the override is coming from.

**Draft reply:**

> Hi there, I can help you track down where the production configuration values are coming from in your staging environment. Based on our documentation, configuration differences between environments are often caused by scope overrides or hidden environment overrides.
> 
> Please try the following steps to identify the source:
> 1. Check the scope at which the variable was defined. Service scope overrides project scope, and project scope overrides organisation defaults [DOC-DEPLOY-004].
> 2. Review the environment overrides page, which lists values that differ from the defaults for each environment [DOC-DEPLOY-004].
> 3. If you make any changes to the configuration, remember to redeploy the service, as running containers do not pick up new values without a restart [DOC-DEPLOY-004].
> 
> Let me know if you find the override or if you need further assistance.

**Retrieved passages:**

- **DOC-DEPLOY-004 (cited)**, Configuring environment variables and secrets: # Configuring environment variables and secrets

**Applies to:** All compute services

## Symptoms

- The application cannot read a variable that appears to be set
- A secret value appears in plain text in the logs
- Configuration differs between environments unexpectedly

## Common causes

- The variable was set at project scope but read at service scope
- The application logs its configuration at startup
- An environment override exists that is not visible on the main settings page

## Resolution

- **DOC-DEPLOY-004 (cited)**, Configuring environment variables and secrets: ## Resolution

1. Check the scope at which the variable was defined. Service scope overrides project scope, and project scope overrides organisation defaults.
2. Store anything sensitive as a secret rather than a variable. Secrets are masked in logs and are not readable through the API after creation.
3. Review the environment overrides page, which lists values that differ from the defaults for each environment.
4. Redeploy after changing configuration. Running containers do not pick up new values without a restart.

## Notes

A secret that has been printed to logs should be treated as exposed and rotated, even if the logs are private.

- **DOC-BILL-003**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

- **DOC-DEPLOY-002**, Rolling back a failed release: ## Resolution

1. Open the revisions page for the service and identify the last revision that was healthy.
2. Select roll back on that revision. Traffic moves within roughly thirty seconds and no rebuild takes place.
3. If the release included a database migration, roll the migration back before the service, or the older code will encounter a schema it does not expect.
4. Record the incident and the reason for the rollback before deploying a fix, while the detail is still fresh.

## Notes

Rollback restores the container image and its configuration together. It does not restore data.

- **DOC-SEC-002**, Handling exposed secrets and credential rotation: # Handling exposed secrets and credential rotation

**Applies to:** All plans

## Symptoms

- A key has been committed to a repository
- A secret appears in application logs
- A third party has reported finding a credential

## Common causes

- Configuration was committed rather than referenced from the environment
- The application prints its configuration during startup
- A key was shared in a support ticket or a chat message

## Resolution

---

## 43. VAL-0066

**Channel:** forum | **Customer plan:** enterprise

**Subject:** Question about backup regions

**Ticket body:**

> one of our customers has asked for written confirmation of where their data is physically stored. Can you please point me to something I can share with them? sorry for my english.

**Draft reply:**

> Hello,
> 
> You can share the following information with your customer regarding where their data is physically stored:
> 
> 1. Primary Data: The region shown on the organisation settings page determines where primary data is stored. This region is fixed at the time of creation [DOC-DATA-003].
> 2. Backups: By default, backups are replicated to a second region [DOC-DATA-003]. If a single-region requirement applies, the backup replication setting should be reviewed [DOC-DATA-003].
> 3. Metadata: Please note that metadata, such as account names and billing records, is stored centrally regardless of the selected data region [DOC-DATA-003].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-DATA-003 (cited)**, Data residency and regional storage: # Data residency and regional storage

**Applies to:** Business and Enterprise plans

## Symptoms

- A customer requires data to remain in a specific region
- Latency is high for users far from the primary region
- A compliance review has asked where data is held

## Common causes

- The organisation was created in a region that no longer suits the requirement
- Read traffic is being served from the primary region only
- Backups are replicated to a second region by default

## Resolution

- **DOC-DATA-003 (cited)**, Data residency and regional storage: ## Resolution

1. Check the region shown on the organisation settings page. This is fixed at creation and determines where primary data is stored.
2. Enable read replicas in additional regions to reduce latency for distant users without moving primary storage.
3. Review the backup replication setting if a single-region requirement applies, since cross-region replication is enabled by default.
4. Migrating an organisation between regions requires a planned migration with support and involves a maintenance window.

## Notes

Metadata such as account names and billing records is stored centrally regardless of the data region.

- **DOC-DATA-002**, Backups, retention and point-in-time restore: # Backups, retention and point-in-time restore

**Applies to:** Managed Database

## Symptoms

- Data was deleted and needs recovering
- A restore is taking longer than expected
- A backup is older than expected

## Common causes

- Automated backups run daily and retention depends on the plan
- Restore time scales with database size
- Point-in-time recovery is available only where continuous archiving is enabled

## Resolution

- **DOC-DATA-002**, Backups, retention and point-in-time restore: ## Resolution

1. Identify the point you need to restore to. Point-in-time recovery covers any moment within the retention window rather than only backup times.
2. Restore into a new database instance rather than over the existing one, so the current state is preserved while you verify the restore.
3. Allow roughly ten minutes per hundred gigabytes for the restore, and considerably longer where the instance is also under load.
4. Verify the restored data before switching traffic, and keep the original instance until that verification is complete.

## Notes

Retention is seven days on Standard, thirty days on Business and ninety days on Enterprise plans.

- **DOC-ONB-002**, Migrating an existing application to CloudServe: ## Resolution

1. Externalise configuration before migrating. Anything read from a file on disk should move to environment variables or secrets.
2. Identify local state such as uploaded files or session data and move it to object storage or the managed database first.
3. Run in parallel with the existing deployment and shift a small share of traffic before committing to the move.
4. Plan the database migration separately from the application migration; attempting both at once makes any failure hard to diagnose.

## Notes

Applications that write to the local filesystem will lose that data on every deployment and every scaling event.

---

## 44. VAL-0027

**Channel:** email | **Customer plan:** enterprise

**Subject:** Usage allowance already consumed

**Ticket body:**

> Overage charges appeared on our invoice that we were not expecting. We thought we were well inside our allowance.

**Draft reply:**

> Hi there,
> 
> I understand that unexpected overage charges have appeared on your invoice. This can happen if the plan allowance is consumed before the end of the billing period, or if overage protection is disabled, allowing usage to continue beyond the allowance at the listed rate [DOC-BILL-003]. Additionally, resources in staging or development environments are billed at the same rate as production, which can contribute to higher-than-expected usage [DOC-BILL-001].
> 
> To investigate, please open the usage breakdown for the period on your billing page, which itemises charges by service and environment [DOC-BILL-001]. You should also check the billing period dates at the top of the invoice, as the period runs from the anniversary of your subscription date rather than the calendar month [DOC-BILL-001].
> 
> To prevent this in the future, I recommend setting usage alerts at 50%, 80%, and 95% of your allowance so you can monitor accrual during the period [DOC-BILL-003]. You can also decide between a hard spend cap, which stops the service, and overage, which continues at the listed rate [DOC-BILL-003].
> 
> Please note that invoices are finalised three days after the period ends. If you request an adjustment before finalisation, it will appear on the same invoice [DOC-BILL-001].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-003 (cited)**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

- **DOC-BILL-003 (cited)**, Usage limits, overage and spend controls: ## Resolution

1. Check the current period usage against the plan allowance on the billing page.
2. Decide deliberately between a hard spend cap, which stops the service, and overage, which continues at the listed rate. Production workloads generally need the second.
3. Configure alerts at fifty, eighty and ninety-five per cent of allowance rather than relying on the cap as a warning.
4. Where a cap has stopped a production service, an account owner can raise it immediately from the billing page and service resumes within a minute.

## Notes

Spend caps apply per organisation and cannot currently be set per project.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

---

## 45. VAL-0018

**Channel:** email | **Customer plan:** enterprise

**Subject:** How do I page through large results

**Ticket body:**

> Our cursor seems to stop working partway through a long iteration. Is there an expiry we should be handling?

**Draft reply:**

> Hi there,
> 
> Yes, cursors do expire. According to our documentation, cursors expire after one hour [DOC-API-002]. If your iteration is taking longer than that, the cursor will become invalid, which likely explains why it stops working partway through.
> 
> To handle this, you should implement a checkpointing strategy. When a cursor expires, restart the iteration from your last recorded checkpoint [DOC-API-002]. Additionally, ensure you are passing the `next_cursor` value from each response as the `cursor` parameter for the next request, and stop when it is null [DOC-API-002].
> 
> If you are dealing with very large extracts, you might also consider using the export endpoint, which runs asynchronously and returns a download link [DOC-API-002].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-API-002 (cited)**, Pagination and handling large result sets: ## Resolution

1. Use cursor pagination for anything that may change while you iterate. Offset pagination will skip or repeat records when items are inserted mid-iteration.
2. Pass the next_cursor value from each response as the cursor parameter of the following request, and stop when it is null.
3. Keep page size at or below two hundred. Larger requests are rejected rather than truncated.
4. For very large extracts, use the export endpoint, which runs asynchronously and returns a download link.

## Notes

Cursors expire after one hour. Long-running iterations should handle expiry by restarting from a recorded checkpoint.

- **DOC-API-002 (cited)**, Pagination and handling large result sets: # Pagination and handling large result sets

**Applies to:** All plans

## Symptoms

- Only the first page of results is returned
- Iterating through results misses or duplicates records
- Large queries time out

## Common causes

- The cursor from the previous response was not passed to the next request
- Offset pagination was used against a changing collection
- The page size requested exceeds the maximum

## Resolution

- **DOC-API-001**, Understanding API rate limits and quota tiers: ## Resolution

1. Read the rate limit headers returned with every response. They give the limit, the remaining allowance and the reset time, which is more reliable than inferring the limit from behaviour.
2. Confirm whether the endpoint has a specific limit. Search and export endpoints are more expensive and are limited more tightly than reads.
3. Implement exponential backoff with jitter on 429 responses rather than retrying immediately, which prolongs the throttling.
4. Where sustained higher throughput is genuinely required, the limit can be raised on Business and Enterprise plans through an account request.

## Notes

Limits are enforced per organisation. Issuing more keys does not increase the available quota.

- **DOC-DATA-001**, Exporting account data and scheduled extracts: ## Resolution

1. Check the exports page for job status. Jobs covering more than a million records commonly take several minutes.
2. Request a fresh link from the exports page if the original has expired. The underlying file is retained for seven days.
3. Note that the export reflects the moment the job began, so records created during processing are not included.
4. For recurring needs, configure a scheduled export delivered to object storage rather than generating them manually.

## Notes

Exports containing personal data are logged in the audit trail with the requesting user and the fields included.

- **DOC-PERF-003**, Database connection pool exhaustion: # Database connection pool exhaustion

**Applies to:** Managed Database

## Symptoms

- Errors indicating no connection is available
- Latency increases sharply as traffic grows
- The database reports far fewer active queries than the application expects

## Common causes

- The pool size multiplied by the instance count exceeds the database connection limit
- Connections are not being returned to the pool after use
- Long-running transactions are holding connections open

## Resolution

---

## 46. VAL-0071

**Channel:** docs_comment | **Customer plan:** standard

**Subject:** Spend cap stopped our service

**Ticket body:**

> We were throttled over the weekend after a traffic increase and it took down part of our product. We would rather pay overage than be stopped. How do we change that?

**Draft reply:**

> Hi there, I'm sorry to hear that the spend cap interrupted your service. To switch from a hard cap to overage billing, you can configure your spend controls on the billing page [DOC-BILL-003]. You should choose overage, which allows usage to continue at the listed rate, rather than a hard cap, which stops the service [DOC-BILL-003]. If the cap has already stopped your service, an account owner can raise it immediately from the billing page, and the service should resume within a minute [DOC-BILL-003]. Additionally, it is recommended to set usage alerts at 50%, 80%, and 95% of your allowance to monitor usage proactively [DOC-BILL-003].

**Retrieved passages:**

- **DOC-BILL-003 (cited)**, Usage limits, overage and spend controls: ## Resolution

1. Check the current period usage against the plan allowance on the billing page.
2. Decide deliberately between a hard spend cap, which stops the service, and overage, which continues at the listed rate. Production workloads generally need the second.
3. Configure alerts at fifty, eighty and ninety-five per cent of allowance rather than relying on the cap as a warning.
4. Where a cap has stopped a production service, an account owner can raise it immediately from the billing page and service resumes within a minute.

## Notes

Spend caps apply per organisation and cannot currently be set per project.

- **DOC-BILL-003 (cited)**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-API-001**, Understanding API rate limits and quota tiers: ## Resolution

1. Read the rate limit headers returned with every response. They give the limit, the remaining allowance and the reset time, which is more reliable than inferring the limit from behaviour.
2. Confirm whether the endpoint has a specific limit. Search and export endpoints are more expensive and are limited more tightly than reads.
3. Implement exponential backoff with jitter on 429 responses rather than retrying immediately, which prolongs the throttling.
4. Where sustained higher throughput is genuinely required, the limit can be raised on Business and Enterprise plans through an account request.

## Notes

Limits are enforced per organisation. Issuing more keys does not increase the available quota.

- **DOC-BILL-001**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

---

## 47. VAL-0077

**Channel:** chat | **Customer plan:** business

**Subject:** 

**Ticket body:**

> Our billing period does not seem to match the calendar month, which is making reconciliation difficult. Is that expected?

**Draft reply:**

> Yes, this is expected. The billing period runs from the anniversary of your subscription date rather than the first of the calendar month [DOC-BILL-001]. To assist with reconciliation, you can check the specific billing period dates at the top of your invoice [DOC-BILL-001]. Additionally, invoices are finalized three days after the period ends [DOC-BILL-001].

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-DATA-003**, Data residency and regional storage: ## Resolution

1. Check the region shown on the organisation settings page. This is fixed at creation and determines where primary data is stored.
2. Enable read replicas in additional regions to reduce latency for distant users without moving primary storage.
3. Review the backup replication setting if a single-region requirement applies, since cross-region replication is enabled by default.
4. Migrating an organisation between regions requires a planned migration with support and involves a maintenance window.

## Notes

Metadata such as account names and billing records is stored centrally regardless of the data region.

---

## 48. VAL-0059

**Channel:** docs_comment | **Customer plan:** enterprise

**Subject:** Config differs between environments

**Ticket body:**

> Where should secrets be stored so they do not appear in the logs? At the moment ours are being printed at startup and I am not comfortable with that.

**Draft reply:**

> Hi there,
> 
> To prevent secrets from appearing in your logs, you should store them as secrets rather than standard environment variables. Secrets are masked in logs and are not readable through the API after creation [DOC-DEPLOY-004].
> 
> Since your secrets are currently being printed at startup, please treat them as exposed and rotate them immediately, even if your logs are private [DOC-DEPLOY-004]. To rotate them, you should first revoke the exposed credentials, then issue replacements with the narrowest scope that still works [DOC-SEC-002]. Additionally, it is recommended to search your audit log for any use of the exposed credentials from unfamiliar addresses during the time they were exposed [DOC-SEC-002].
> 
> After updating your configuration, remember to redeploy your service, as running containers do not pick up new values without a restart [DOC-DEPLOY-004].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-DEPLOY-004 (cited)**, Configuring environment variables and secrets: # Configuring environment variables and secrets

**Applies to:** All compute services

## Symptoms

- The application cannot read a variable that appears to be set
- A secret value appears in plain text in the logs
- Configuration differs between environments unexpectedly

## Common causes

- The variable was set at project scope but read at service scope
- The application logs its configuration at startup
- An environment override exists that is not visible on the main settings page

## Resolution

- **DOC-DEPLOY-004 (cited)**, Configuring environment variables and secrets: ## Resolution

1. Check the scope at which the variable was defined. Service scope overrides project scope, and project scope overrides organisation defaults.
2. Store anything sensitive as a secret rather than a variable. Secrets are masked in logs and are not readable through the API after creation.
3. Review the environment overrides page, which lists values that differ from the defaults for each environment.
4. Redeploy after changing configuration. Running containers do not pick up new values without a restart.

## Notes

A secret that has been printed to logs should be treated as exposed and rotated, even if the logs are private.

- **DOC-SEC-002 (cited)**, Handling exposed secrets and credential rotation: # Handling exposed secrets and credential rotation

**Applies to:** All plans

## Symptoms

- A key has been committed to a repository
- A secret appears in application logs
- A third party has reported finding a credential

## Common causes

- Configuration was committed rather than referenced from the environment
- The application prints its configuration during startup
- A key was shared in a support ticket or a chat message

## Resolution

- **DOC-SEC-001**, Responding to a suspected account compromise: # Responding to a suspected account compromise

**Applies to:** All plans

## Symptoms

- Unrecognised activity appears in the audit log
- A user reports credentials may have been exposed
- Resources were created that nobody claims

## Common causes

- Credentials were reused from a service that suffered a breach
- An API key was committed to a public repository
- A former team member retained access after leaving

## Resolution

- **DOC-SEC-002 (cited)**, Handling exposed secrets and credential rotation: ## Resolution

1. Revoke the exposed credential first. Removing it from the repository does not help, because it remains in the history.
2. Issue a replacement with the narrowest scope that still works, rather than recreating the original permissions by default.
3. Search the audit log for use of the exposed credential from unfamiliar addresses during the exposure window.
4. Add secret scanning to your pipeline so that the next occurrence is caught before it reaches a remote branch.

## Notes

Never send a live credential to support. Support will never ask for one, and any credential shared in a ticket must be treated as exposed.

---

## 49. VAL-0041

**Channel:** email | **Customer plan:** business

**Subject:** Question about this month's charges

**Ticket body:**

> There are charges on our invoice for a service I do not believe we use. Could you explain what these relate to?

**Draft reply:**

> Hi there,
> 
> I can help explain the charges on your invoice. Charges for a service you do not believe you use can occur for a few reasons, such as usage-based charges accruing beyond your plan allowance, a resource being left running in a non-production environment, or the billing period running from your subscription date rather than the first of the month [DOC-BILL-001]. 
> 
> To identify the specific cause, please open the usage breakdown for the period, which itemises charges by service and by environment [DOC-BILL-001]. You should look for resources in staging or development environments, as these are billed at the same rate as production [DOC-BILL-001]. Additionally, check the billing period dates at the top of the invoice, as the period runs from the anniversary of your subscription date [DOC-BILL-001]. 
> 
> If you find that the charges are unexpected, please let me know the specific service or line item so I can assist you further. You can also set a usage alert on the billing page to notice unexpected accrual during the period rather than at the end of it [DOC-BILL-001].
> 
> Best regards,
> Support Team

**Retrieved passages:**

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: # Understanding your invoice and usage breakdown

**Applies to:** All plans

## Symptoms

- The invoice is higher than expected
- Charges appear for a service that is not in use
- The billing period does not align with the calendar month

## Common causes

- Usage-based charges accrued beyond the plan allowance
- A resource was left running in a non-production environment
- The billing period runs from the subscription date rather than the first of the month

## Resolution

- **DOC-BILL-001 (cited)**, Understanding your invoice and usage breakdown: ## Resolution

1. Open the usage breakdown for the period, which itemises charges by service and by environment.
2. Look for resources in staging or development environments, which are billed at the same rate as production.
3. Check the billing period dates at the top of the invoice. The period runs from the anniversary of the subscription date.
4. Set a usage alert on the billing page so that unexpected accrual is noticed during the period rather than at the end of it.

## Notes

Invoices are finalised three days after the period ends. Adjustments requested before finalisation appear on the same invoice.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: ## Resolution

1. Upgrades take effect immediately and are prorated for the days remaining in the period. The invoice shows the calculation as a separate line.
2. Downgrades take effect at the start of the next period so that paid-for capacity is not lost. The scheduled change appears on the subscription page.
3. Credits from a downgrade or an adjustment are applied against the next invoice by default rather than refunded to the payment method.
4. Where a refund rather than a credit is required, an account owner should raise the request within thirty days of the invoice.

## Notes

Annual plans cannot be downgraded mid-term, but capacity can be reduced with effect from the renewal date.

- **DOC-BILL-002**, Changing plans, and how proration is calculated: # Changing plans, and how proration is calculated

**Applies to:** All plans

## Symptoms

- The charge after an upgrade differs from the advertised price
- A downgrade did not take effect immediately
- A credit is expected but not visible

## Common causes

- The upgrade was prorated across the remainder of the billing period
- Downgrades are applied at the end of the current period rather than immediately
- The credit was applied to the next invoice rather than refunded

## Resolution

- **DOC-BILL-003**, Usage limits, overage and spend controls: # Usage limits, overage and spend controls

**Applies to:** All plans

## Symptoms

- Service was throttled after a traffic increase
- Overage charges appeared unexpectedly
- A spend cap stopped a production workload

## Common causes

- Plan allowance was consumed before the end of the period
- A spend cap was configured and reached
- Overage protection is disabled, so usage continued beyond the allowance

## Resolution

---

## 50. VAL-0019

**Channel:** email | **Customer plan:** business

**Subject:** Remove a departing team member

**Ticket body:**

> my team member not able to open project. i give permission already two time. still not working.

**Draft reply:**

> Hi there,
> 
> I understand your team member is unable to open the project despite you granting permissions twice. Based on our documentation, here are the most common reasons for this issue and how to resolve it:
> 
> 1. **Check Effective Permissions:** Please check the effective permissions view for the user. This view resolves direct roles and group memberships together, which can sometimes show broader or different access than expected [DOC-ACCT-001].
> 2. **Verify Invitation Status:** Confirm that the invitation was actually accepted. Pending invitations appear in a separate section and expire after seven days. If the invitation expired or was not accepted, the account may not exist or the access may not be active [DOC-ACCT-001].
> 3. **Scope of Permissions:** Ensure the role was granted at the correct scope. Sometimes roles are granted at the project scope rather than the organisation scope, or vice versa, which can cause access issues [DOC-ACCT-001].
> 
> If the user is a departing team member who needs to be removed, please remove the user rather than only changing their password, and revoke any API keys they created [DOC-ACCT-001].
> 
> Please let me know if you need further assistance after checking these steps.

**Retrieved passages:**

- **DOC-ACCT-001 (cited)**, Managing team members, roles and permissions: # Managing team members, roles and permissions

**Applies to:** All plans

## Symptoms

- A user cannot access a project they should be able to
- A departing user needs removing
- Permissions need narrowing after a review

## Common causes

- The role was granted at project scope rather than organisation scope
- The invitation was never accepted and the account does not exist
- A group membership grants broader access than the direct role suggests

## Resolution

- **DOC-ACCT-001 (cited)**, Managing team members, roles and permissions: ## Resolution

1. Check the effective permissions view for the user, which resolves direct roles and group memberships together.
2. Confirm the invitation was accepted. Pending invitations appear in a separate section and expire after seven days.
3. Remove a departing user rather than only changing their password, and revoke any API keys they created.
4. Prefer group membership to direct role assignment, so that access can be reviewed in one place.

## Notes

Removing the last account owner is not permitted. Transfer ownership before removing the account.

- **DOC-SEC-001**, Responding to a suspected account compromise: ## Resolution

1. Revoke all API keys for the affected account immediately. This is disruptive and it is the correct first action.
2. Force a password reset and terminate active sessions for the affected users from the team members page.
3. Review the audit log for the period in question, filtering by the affected user, and record anything unexpected before it ages out.
4. Enable multi-factor authentication for all users if it is not already mandatory for the organisation.

## Notes

Audit logs are retained for ninety days on Business plans and one year on Enterprise. Export them promptly during an investigation.

- **DOC-AUTH-001**, Resolving invalid credential errors on login: ## Resolution

1. Confirm whether the account is locked by checking the security page of the console. A locked account displays a red banner and unlocks automatically after thirty minutes.
2. Clear cookies for the CloudServe domain, or open a private browsing window, then attempt the login again.
3. If the CLI is failing, run `cloudserve auth logout` followed by `cloudserve auth login` to discard the cached token.
4. Where the account remains locked and the customer needs immediate access, an administrator on the account can release the lock from the team members page.

## Notes

Repeated lockouts within a short period usually indicate an automated process still using an old password rather than a user error.

- **DOC-AUTH-004**, API key rotation and scope management: ## Resolution

1. Check the API keys page for the key's status and expiry. Revoked and expired keys are listed with the date and the user who acted.
2. Review the scopes attached to the key. Read-only keys cannot write, and project-scoped keys cannot reach organisation endpoints.
3. To rotate without downtime, create the replacement key first, deploy it, confirm traffic has moved, then revoke the old key.
4. If a key has been exposed publicly, revoke it immediately rather than waiting for the rotation window.

## Notes

Keys issued to individual users are removed when that user is deleted. Use service accounts for anything running in production.

---
