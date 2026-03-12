# Scripts Cleanup Plan

## Scripts to KEEP (Utility & Admin)

1. **create_admin_user.py** - ✅ Valid - Creates admin user
2. **create_super_admin.py** - ✅ Valid - Creates super admin
3. **process_received_emails.py** - ✅ Valid - Manual email processing utility
4. **reprocess_emails.py** - ✅ Valid - Reset failed emails for reprocessing
5. **run_workers.py** - ✅ Valid - Worker orchestration script

## Scripts to DELETE (Outdated/Duplicate Seed Scripts)

1. **add_conversation_linking_to_worker.py** - Migration/fix script, not needed
2. **amitscomprehensive_seed_data.py** - User-specific, duplicate
3. **create_comprehensive_seed.py** - Duplicate
4. **create_full_seed_data.py** - Duplicate
5. **create_inbound_leads_seed.py** - Specific seed, duplicate
6. **create_production_seed_data.py** - Duplicate
7. **create_seed_data.py** - Duplicate
8. **create_seed_data_for_user.py** - Duplicate
9. **create_seed_for_amits.py** - User-specific, duplicate
10. **create_test_user_seed.py** - Duplicate
11. **create_topleaders_list.py** - Specific feature seed
12. **fix_lead_intent_keywords.py** - One-time fix script
13. **seed_campaign_data.py** - Specific seed, duplicate
14. **setup_complete_system.py** - Duplicate
15. **test_conversation_linking.py** - Test script

Total: 5 scripts to keep, 15 scripts to delete
