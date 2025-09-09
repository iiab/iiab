
local flex = require('flex-base')







flex.set_main_tags('admin') -- or 'all_boundaries' if it's not too big? if it's more useful educational info

flex.modify_main_tags('natural')



-- flex.modify_main_tags('poi/delete')
flex.set_name_tags('core')

-- flex.modify_name_tags('poi')

flex.set_address_tags('core')
flex.set_postcode_fallback(false)

flex.ignore_keys('metatags')
flex.add_for_extratags('required')

flex.ignore_keys('name')
flex.ignore_keys('address')



return flex
