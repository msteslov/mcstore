# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: stats.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'stats.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import auth_pb2 as auth__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bstats.proto\x12\x05stats\x1a\nauth.proto\"\x99\x01\n\x13PlayerStatsResponse\x12\"\n\x05stats\x18\x01 \x01(\x0b\x32\x11.stats.PlayerInfoH\x00\x12\x35\n\x05\x65rror\x18\x02 \x01(\x0e\x32$.stats.PlayerStatsResponse.ErrorTypeH\x00\"\x1f\n\tErrorType\x12\x12\n\x0eunknown_player\x10\x00\x42\x06\n\x04\x62ody\"1\n\x0e\x42lockStatEntry\x12\x10\n\x08\x62lock_id\x18\x01 \x01(\t\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\"=\n\rBaseStatEntry\x12\x1d\n\x04type\x18\x01 \x01(\x0e\x32\x0f.stats.BaseStat\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\"N\n\rItemStatEntry\x12\x1d\n\x04type\x18\x01 \x01(\x0e\x32\x0f.stats.ItemStat\x12\x0f\n\x07item_id\x18\x02 \x01(\t\x12\r\n\x05\x63ount\x18\x03 \x01(\x05\"T\n\x0f\x45ntityStatEntry\x12\x1f\n\x04type\x18\x01 \x01(\x0e\x32\x11.stats.EntityStat\x12\x11\n\tentity_id\x18\x02 \x01(\t\x12\r\n\x05\x63ount\x18\x03 \x01(\x05\"\xd5\x01\n\nPlayerInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04uuid\x18\x02 \x01(\t\x12(\n\nbase_stats\x18\x03 \x03(\x0b\x32\x14.stats.BaseStatEntry\x12)\n\nmine_stats\x18\x04 \x03(\x0b\x32\x15.stats.BlockStatEntry\x12,\n\x0c\x65ntity_stats\x18\x05 \x03(\x0b\x32\x16.stats.EntityStatEntry\x12(\n\nitem_stats\x18\x06 \x03(\x0b\x32\x14.stats.ItemStatEntry*\xdd\x0c\n\x08\x42\x61seStat\x12\x10\n\x0c\x64\x61mage_dealt\x10\x00\x12\x10\n\x0c\x64\x61mage_taken\x10\x01\x12\n\n\x06\x64\x65\x61ths\x10\x02\x12\r\n\tmob_kills\x10\x03\x12\x10\n\x0cplayer_kills\x10\x04\x12\x0f\n\x0b\x66ish_caught\x10\x05\x12\x10\n\x0c\x61nimals_bred\x10\x06\x12\x0e\n\nleave_game\x10\x07\x12\x08\n\x04jump\x10\x08\x12\x0e\n\ndrop_count\x10\t\x12\x13\n\x0fplay_one_minute\x10\x0c\x12\x14\n\x10total_world_time\x10\r\x12\x0f\n\x0bwalk_one_cm\x10\x0e\x12\x18\n\x14walk_on_water_one_cm\x10\x0f\x12\x0f\n\x0b\x66\x61ll_one_cm\x10\x10\x12\x0e\n\nsneak_time\x10\x11\x12\x10\n\x0c\x63limb_one_cm\x10\x12\x12\x0e\n\nfly_one_cm\x10\x13\x12\x1b\n\x17walk_under_water_one_cm\x10\x14\x12\x13\n\x0fminecart_one_cm\x10\x15\x12\x0f\n\x0b\x62oat_one_cm\x10\x16\x12\x0e\n\npig_one_cm\x10\x17\x12\x10\n\x0chorse_one_cm\x10\x18\x12\x11\n\rsprint_one_cm\x10\x19\x12\x11\n\rcrouch_one_cm\x10\x1a\x12\x11\n\raviate_one_cm\x10\x1b\x12\x14\n\x10time_since_death\x10\"\x12\x16\n\x12talked_to_villager\x10#\x12\x18\n\x14traded_with_villager\x10$\x12\x15\n\x11\x63\x61ke_slices_eaten\x10%\x12\x13\n\x0f\x63\x61uldron_filled\x10&\x12\x11\n\rcauldron_used\x10\'\x12\x11\n\rarmor_cleaned\x10(\x12\x12\n\x0e\x62\x61nner_cleaned\x10)\x12\x1c\n\x18\x62rewingstand_interaction\x10*\x12\x16\n\x12\x62\x65\x61\x63on_interaction\x10+\x12\x15\n\x11\x64ropper_inspected\x10,\x12\x14\n\x10hopper_inspected\x10-\x12\x17\n\x13\x64ispenser_inspected\x10.\x12\x14\n\x10noteblock_played\x10/\x12\x13\n\x0fnoteblock_tuned\x10\x30\x12\x11\n\rflower_potted\x10\x31\x12\x1b\n\x17trapped_chest_triggered\x10\x32\x12\x15\n\x11\x65nderchest_opened\x10\x33\x12\x12\n\x0eitem_enchanted\x10\x34\x12\x11\n\rrecord_played\x10\x35\x12\x17\n\x13\x66urnace_interaction\x10\x36\x12\x1e\n\x1a\x63rafting_table_interaction\x10\x37\x12\x10\n\x0c\x63hest_opened\x10\x38\x12\x10\n\x0csleep_in_bed\x10\x39\x12\x16\n\x12shulker_box_opened\x10:\x12\x13\n\x0ftime_since_rest\x10;\x12\x0f\n\x0bswim_one_cm\x10<\x12\x19\n\x15\x64\x61mage_dealt_absorbed\x10=\x12\x19\n\x15\x64\x61mage_dealt_resisted\x10>\x12\x1c\n\x18\x64\x61mage_blocked_by_shield\x10?\x12\x13\n\x0f\x64\x61mage_absorbed\x10@\x12\x13\n\x0f\x64\x61mage_resisted\x10\x41\x12\x15\n\x11\x63lean_shulker_box\x10\x42\x12\x0f\n\x0bopen_barrel\x10\x43\x12\x1f\n\x1binteract_with_blast_furnace\x10\x44\x12\x18\n\x14interact_with_smoker\x10\x45\x12\x19\n\x15interact_with_lectern\x10\x46\x12\x1a\n\x16interact_with_campfire\x10G\x12#\n\x1finteract_with_cartography_table\x10H\x12\x16\n\x12interact_with_loom\x10I\x12\x1d\n\x19interact_with_stonecutter\x10J\x12\r\n\tbell_ring\x10K\x12\x10\n\x0craid_trigger\x10L\x12\x0c\n\x08raid_win\x10M\x12\x17\n\x13interact_with_anvil\x10N\x12\x1c\n\x18interact_with_grindstone\x10O\x12\x0e\n\ntarget_hit\x10P\x12 \n\x1cinteract_with_smithing_table\x10Q\x12\x12\n\x0estrider_one_cm\x10R*N\n\x08ItemStat\x12\x08\n\x04\x64rop\x10\x00\x12\n\n\x06pickup\x10\x01\x12\x0c\n\x08use_item\x10\x02\x12\x0e\n\nbreak_item\x10\x03\x12\x0e\n\ncraft_item\x10\x04*3\n\nEntityStat\x12\x0f\n\x0bkill_entity\x10\x00\x12\x14\n\x10\x65ntity_killed_by\x10\x01\x32\x41\n\x05Stats\x12\x38\n\x07getInfo\x12\x0f.stats.PlayerId\x1a\x1a.stats.PlayerStatsResponse\"\x00\x42\x30\n\x19ru.skykatik.tgintegr.grpcB\x11PlayersStatsProtoP\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'stats_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'\n\031ru.skykatik.tgintegr.grpcB\021PlayersStatsProtoP\001'
  _globals['_BASESTAT']._serialized_start=687
  _globals['_BASESTAT']._serialized_end=2316
  _globals['_ITEMSTAT']._serialized_start=2318
  _globals['_ITEMSTAT']._serialized_end=2396
  _globals['_ENTITYSTAT']._serialized_start=2398
  _globals['_ENTITYSTAT']._serialized_end=2449
  _globals['_PLAYERSTATSRESPONSE']._serialized_start=35
  _globals['_PLAYERSTATSRESPONSE']._serialized_end=188
  _globals['_PLAYERSTATSRESPONSE_ERRORTYPE']._serialized_start=149
  _globals['_PLAYERSTATSRESPONSE_ERRORTYPE']._serialized_end=180
  _globals['_BLOCKSTATENTRY']._serialized_start=190
  _globals['_BLOCKSTATENTRY']._serialized_end=239
  _globals['_BASESTATENTRY']._serialized_start=241
  _globals['_BASESTATENTRY']._serialized_end=302
  _globals['_ITEMSTATENTRY']._serialized_start=304
  _globals['_ITEMSTATENTRY']._serialized_end=382
  _globals['_ENTITYSTATENTRY']._serialized_start=384
  _globals['_ENTITYSTATENTRY']._serialized_end=468
  _globals['_PLAYERINFO']._serialized_start=471
  _globals['_PLAYERINFO']._serialized_end=684
  _globals['_STATS']._serialized_start=2451
  _globals['_STATS']._serialized_end=2516
# @@protoc_insertion_point(module_scope)
