# Copyright (c) 2014, 2015, 2016, 2017 Wieland Hoffmann, MetaBrainz Foundation
# License: MIT, see LICENSE for details

"""
This package contains core entities that are used in the search index and
various tools for working with them.
"""

# Below are the defininitions for all search entities. Each defines a set of
# fields and some additional parameters. Entities have paths associated with
# them, which define the way along which values of fields can be found. The
# paths are created manually by reading through the *Index.java files in
# https://github.com/metabrainz/search-server/tree/master/index/src/main/java/org/musicbrainz/search/index
# and figuring out which SQL statements are used for which search field.
#
# Some entities contain an `extrapaths` argument, which has the paths that are
# not stored in search fields, but are in the XML generated by the wscompat
# module. We don't want to interact with the database in the wscompat module
# since it will be very inefficient: for each entity/row that it processes, it
# would fetch additional required data and only for that single entity. So for
# N entites that are processed by the wscompat module, we'd have an additional
# N accesses to the database.
#
# Paths might need to be updated as a part of schema changes in the
# MusicBrainz server.

from sir.schema import queryext
from sir.schema import modelext
from sir.schema import transformfuncs as tfs
from sir.schema.searchentities import SearchEntity as E, SearchField as F
from sir.wscompat import convert
from collections import OrderedDict
from mbdata import models
from collections import defaultdict
from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from sqlalchemy.orm.descriptor_props import CompositeProperty


SearchAnnotation = E(modelext.CustomAnnotation, [
    F("id", "id"),
    F("entity", ["areas.area.gid", "artists.artist.gid", "events.event.gid",
                 "instruments.instrument.gid", "labels.label.gid",
                 "places.place.gid", "recordings.recording.gid",
                 "releases.release.gid", "release_groups.release_group.gid",
                 "series.series.gid", "works.work.gid"]),
    F("name", ["areas.area.name", "artists.artist.name", "events.event.name",
               "instruments.instrument.name", "labels.label.name",
               "places.place.name", "recordings.recording.name",
               "releases.release.name", "release_groups.release_group.name",
               "series.series.name", "works.work.name"]),
    F("text", "text"),
    F("type", ["areas.__tablename__", "artists.__tablename__",
               "events.__tablename__", "instruments.__tablename__",
               "labels.__tablename__", "places.__tablename__",
               "recordings.__tablename__", "releases.__tablename__",
               "release_groups.__tablename__", "series.__tablename__",
               "works.__tablename__"],
      transformfunc=tfs.annotation_type)
],
    1.5,
    convert.convert_annotation,
    extraquery=queryext.filter_valid_annotations
)


SearchArea = E(modelext.CustomArea, [
    F("mbid", "gid"),
    F("area", "name"),
    F("alias", "aliases.name"),
    F("comment", "comment"),
    F("begin", "begin_date", transformfunc=tfs.index_partialdate_to_string),
    F("end", "end_date", transformfunc=tfs.index_partialdate_to_string),
    F("ended", "ended", transformfunc=tfs.ended_to_string),
    F("iso1", "iso_3166_1_codes.code"),
    F("iso2", "iso_3166_2_codes.code"),
    F("iso3", "iso_3166_3_codes.code"),
    F("sortname", "aliases.sort_name"),
    F("ref_count", ["place_count", "label_count", "artist_count"], transformfunc=tfs.integer_sum, trigger=False),
    F("tag", "tags.tag.name"),
    F("type", "type.name")
],
    1.5,
    convert.convert_area,
    extrapaths=["aliases.type.name", "aliases.type.id",
                "aliases.sort_name", "aliases.type.gid",
                "aliases.locale", "aliases.primary_for_locale",
                "aliases.begin_date", "aliases.end_date",
                "area_links.area0.name",
                "area_links.area0.gid",
                "area_links.area0.begin_date",
                "area_links.area0.end_date",
                "area_links.area0.type.id",
                "area_links.area0.type.gid",
                "area_links.link.link_type.name",
                "area_links.link.link_type.gid",
                "area_links.link.attributes.attribute_type.name",
                "area_links.link.attributes.attribute_type.gid",
                "tags.count", "type.gid"
                ]
)


SearchArtist = E(modelext.CustomArtist, [
    F("mbid", "gid"),
    F("artist", "name"),
    F("sortname", "sort_name"),
    F("alias", "aliases.name"),
    # Does not require a trigger since this will get updated on an alias update
    F("primary_alias", "primary_aliases", trigger=False),
    F("begin", "begin_date", transformfunc=tfs.index_partialdate_to_string),
    F("end", "end_date", transformfunc=tfs.index_partialdate_to_string),
    F("ended", "ended", transformfunc=tfs.ended_to_string),

    F("area", ["area.name", "area.aliases.name"]),
    F("beginarea", ["begin_area.name", "begin_area.aliases.name"]),
    F("country", "area.iso_3166_1_codes.code"),
    F("endarea", ["end_area.name", "end_area.aliases.name"]),
    F("ref_count", "artist_credit_names.artist_credit.ref_count",
                    transformfunc=sum, trigger=False),
    F("comment", "comment"),
    F("gender", "gender.name"),
    F("ipi", "ipis.ipi"),
    F("isni", "isnis.isni"),
    F("tag", "tags.tag.name"),
    F("type", "type.name")
],
    1.5,
    convert.convert_artist,
    extrapaths=["tags.count",
                "aliases.type.name", "aliases.type.id",
                "aliases.type.gid", "aliases.sort_name",
                "aliases.locale", "aliases.primary_for_locale",
                "aliases.begin_date", "aliases.end_date",
                "begin_area.gid", "area.gid", "end_area.gid",
                "gender.gid",
                "type.gid"]
)


SearchCDStub = E(modelext.CustomReleaseRaw, [
    F("id", "id"),
    F("title", "title"),
    F("artist", "artist"),
    F("comment", "comment"),
    F("barcode", "barcode"),
    F("added", "added"),
    F("tracks", "discids.track_count"),
    F("discid", "discids.discid")
],
    1.5,
    convert.convert_cdstub
)

SearchEditor = E(models.Editor, [
    F("id", "id"),
    F("bio", "bio"),
    F("editor", "name")
],
    1.5,
    convert.convert_editor
)

SearchEvent = E(modelext.CustomEvent, [
    F("mbid", "gid"),
    F("alias", "aliases.name"),
    F("aid", "area_links.entity0.gid"),
    F("area", "area_links.entity0.name"),
    F("arid", "artist_links.entity0.gid"),
    F("artist", "artist_links.entity0.name"),
    F("pid", "place_links.entity1.gid"),
    F("place", "place_links.entity1.name"),
    F("comment", "comment"),
    F("event", "name"),
    F("tag", "tags.tag.name"),
    F("type", "type.name"),
    F("begin", "begin_date", transformfunc=tfs.index_partialdate_to_string),
    F("ended", "ended", transformfunc=tfs.ended_to_string),
    F("end", "end_date", transformfunc=tfs.index_partialdate_to_string)
],
    1.5,
    convert.convert_event,
    extrapaths=["aliases.type.name",
                "aliases.type.id",
                "aliases.type.gid",
                "aliases.sort_name",
                "aliases.locale",
                "aliases.primary_for_locale",
                "aliases.begin_date",
                "aliases.end_date",
                "area_links.area.name",
                "area_links.area.gid",
                "area_links.link.link_type.name",
                "area_links.link.link_type.gid",
                "area_links.link.attributes.attribute_type.name",
                "area_links.link.attributes.attribute_type.gid",
                "artist_links.artist.gid",
                "artist_links.artist.name",
                "artist_links.artist.comment",
                "artist_links.link.link_type.name",
                "artist_links.link.link_type.gid",
                "artist_links.link.attributes.attribute_type.name",
                "artist_links.link.attributes.attribute_type.gid",
                "place_links.place.gid",
                "place_links.place.name",
                "place_links.link.link_type.name",
                "place_links.link.link_type.gid",
                "place_links.link.attributes.attribute_type.name",
                "place_links.link.attributes.attribute_type.gid",
                "tags.count", "type.gid",
                "time"]
)

SearchInstrument = E(modelext.CustomInstrument, [
    F("alias", "aliases.name"),
    F("comment", "comment"),
    F("description", "description"),
    F("mbid", "gid"),
    F("instrument", "name"),
    F("tag", "tags.tag.name"),
    F("type", "type.name")
],
    1.5,
    convert.convert_instrument,
    extrapaths=["aliases.type.name", "aliases.type.id",
                "aliases.sort_name", "aliases.type.gid",
                "aliases.locale", "aliases.primary_for_locale",
                "aliases.begin_date", "aliases.end_date", "tags.count", "type.gid"]
)


SearchLabel = E(modelext.CustomLabel, [
    F("mbid", "gid"),
    F("label", "name"),
    F("alias", "aliases.name"),
    F("area", ["area.name", "area.aliases.name"]),
    F("country", "area.iso_3166_1_codes.code"),
    F("begin", "begin_date", transformfunc=tfs.index_partialdate_to_string),
    F("end", "end_date", transformfunc=tfs.index_partialdate_to_string),
    F("ended", "ended", transformfunc=tfs.ended_to_string),

    F("code", "label_code"),
    F("comment", "comment"),
    F("release_count", "release_count", transformfunc=tfs.integer_sum, trigger=False),
    F("sortname", "aliases.sort_name"),
    F("ipi", "ipis.ipi"),
    F("isni", "isnis.isni"),
    F("tag", "tags.tag.name"),
    F("type", "type.name")
],
    1.5,
    convert.convert_label,
    extrapaths=["aliases.type.name", "aliases.type.id",
                "aliases.type.gid", "aliases.sort_name",
                "aliases.locale", "aliases.primary_for_locale",
                "aliases.begin_date", "aliases.end_date",
                "area.gid", "area.type.name", "area.type.gid",
                "tags.count", "type.gid"
                ]
)


SearchPlace = E(modelext.CustomPlace, [
    F("mbid", "gid"),
    F("address", "address"),
    F("alias", "aliases.name"),
    F("area", ["area.name", "area.aliases.name"]),
    F("begin", "begin_date", transformfunc=tfs.index_partialdate_to_string),
    F("comment", "comment"),
    F("end", "end_date", transformfunc=tfs.index_partialdate_to_string),
    F("ended", "ended", transformfunc=tfs.ended_to_string),
    F("lat", "coordinates", transformfunc=tfs.lat),
    F("long", "coordinates", transformfunc=tfs.long),
    F("place", "name"),
    F("type", "type.name")
],
    1.5,
    convert.convert_place,
    extrapaths=["aliases.type.name", "aliases.type.id",
                "aliases.type.gid", "aliases.sort_name",
                "aliases.locale", "aliases.primary_for_locale",
                "aliases.begin_date", "aliases.end_date",
                "area.gid", "type.gid"]
)


SearchRecording = E(modelext.CustomRecording, [
    F("alias", "aliases.name"),
    F("arid", "artist_credit.artists.artist.gid"),
    F("artist", "artist_credit.name"),
    F("artistname", "artist_credit.artists.artist.name"),
    F("comment", "comment"),
    F("country", "tracks.medium.release.country_dates.country.area.iso_3166_1_codes.code"),
    F("creditname", "artist_credit.artists.name"),
    F("date", "tracks.medium.release.country_dates.date",
      transformfunc=tfs.index_partialdate_to_string),
    F("dur", "length"),
    F("format", "tracks.medium.format.name"),
    F("isrc", "isrcs.isrc"),
    F("mbid", "gid"),
    F("number", "tracks.number"),
    F("position", "tracks.medium.position"),
    F("primarytype", "tracks.medium.release.release_group.type.name"),
    F("qdur", "length", transformfunc=tfs.qdur),
    F("recording", "name"),
    F("reid", "tracks.medium.release.gid"),
    F("release", "tracks.medium.release.name"),
    F("rgid", "tracks.medium.release.release_group.gid"),
    F("secondarytype",
      "tracks.medium.release.release_group.secondary_types.secondary_type."
      "name"),
    F("status", "tracks.medium.release.status.name"),
    F("tag", "tags.tag.name"),
    F("tid", "tracks.gid"),
    F("tnum", "tracks.position"),
    F("tracks", "tracks.medium.track_count"),
    F("tracksrelease", "tracks.medium.release.mediums.track_count",
        transformfunc=sum),
    F("video", "video", transformfunc=tfs.boolean)
],
    1.5,
    convert.convert_recording,
    extrapaths=["artist_credit.artists.artist.aliases.begin_date",
                "artist_credit.artists.artist.aliases.end_date",
                "artist_credit.artists.artist.aliases.locale",
                "artist_credit.artists.artist.aliases.name",
                "artist_credit.artists.artist.aliases.primary_for_locale",
                "artist_credit.artists.artist.aliases.sort_name",
                "artist_credit.artists.artist.aliases.type.id",
                "artist_credit.artists.artist.aliases.type.name",
                "artist_credit.artists.artist.aliases.type.gid",
                "artist_credit.artists.artist.comment",
                "artist_credit.artists.artist.gid",
                "artist_credit.artists.artist.name",
                "artist_credit.artists.artist.sort_name",
                "artist_credit.artists.join_phrase",
                "artist_credit.artists.name",
                "artist_credit.name",
                "tags.count",
                "tags.tag.name",
                "tracks.length",
                "tracks.medium.cdtocs.id",
                "tracks.medium.release.artist_credit.artists.artist.comment",
                "tracks.medium.release.artist_credit.artists.artist.gid",
                "tracks.medium.release.artist_credit.artists.artist.name",
                "tracks.medium.release.artist_credit.artists.artist.sort_name",
                "tracks.medium.release.artist_credit.artists.join_phrase",
                "tracks.medium.release.artist_credit.artists.name",
                "tracks.medium.release.artist_credit.name",
                "tracks.medium.release.comment",
                "tracks.medium.release.country_dates.country.area.gid",
                "tracks.medium.release.country_dates.country.area."
                "iso_3166_1_codes.code",
                "tracks.medium.release.country_dates.country.area.name",
                "tracks.medium.release.country_dates.date_day",
                "tracks.medium.release.country_dates.date_month",
                "tracks.medium.release.country_dates.date_year",
                "tracks.medium.release.release_group.comment",
                "tracks.medium.release.release_group.name",
                "tracks.medium.release.release_group.type.gid",
                "tracks.medium.release.release_group.secondary_types.secondary_type.gid",
                "tracks.medium.release.status.gid",
                "tracks.name"]
)


SearchRelease = E(modelext.CustomRelease, [
    F("mbid", "gid"),
    F("release", "name"),
    F("alias", "aliases.name"),
    F("arid", "artist_credit.artists.artist.gid"),
    F("artist", "artist_credit.name"),
    F("artistname", "artist_credit.artists.artist.name"),
    F("asin", "asin.amazon_asin"),
    F("creditname", "artist_credit.artists.name"),
    F("country", "country_dates.country.area.iso_3166_1_codes.code"),
    F("date", "country_dates.date",
      transformfunc=tfs.index_partialdate_to_string),
    F("barcode", "barcode", transformfunc=tfs.fill_none),
    F("catno", "labels.catalog_number"),
    F("comment", "comment"),
    F("format", "mediums.format.name"),
    F("laid", "labels.label.gid"),
    F("label", "labels.label.name"),
    F("lang", "language.iso_code_3"),
    F("mediums", "medium_count", transformfunc=tfs.integer_sum, trigger=False),
    F("primarytype", "release_group.type.name"),
    F("quality", "quality"),
    F("rgid", "release_group.gid"),
    F("script", "script.iso_code"),
    F("secondarytype", "release_group.secondary_types.secondary_type.name"),
    F("status", "status.name"),
    F("tracks", "mediums.track_count",
      transformfunc=sum),
    F("tracksmedium", "mediums.track_count"),
    F("tag", "tags.tag.name")
],
    1.5,
    convert.convert_release,
    extrapaths=["artist_credit.artists.join_phrase",
                "artist_credit.artists.artist.aliases.begin_date",
                "artist_credit.artists.artist.aliases.end_date",
                "artist_credit.artists.artist.aliases.locale",
                "artist_credit.artists.artist.aliases.name",
                "artist_credit.artists.artist.aliases.primary_for_locale",
                "artist_credit.artists.artist.aliases.sort_name",
                "artist_credit.artists.artist.aliases.type.id",
                "artist_credit.artists.artist.aliases.type.name",
                "artist_credit.artists.artist.aliases.type.gid",
                "artist_credit.artists.artist.gid",
                "artist_credit.artists.artist.sort_name",
                "country_dates.country.area.gid",
                "country_dates.country.area.name",
                "country_dates.country.area.iso_3166_1_codes.code",
                "country_dates.date_day",
                "country_dates.date_month",
                "country_dates.date_year",
                "mediums.cdtocs.id",
                "packaging.name",
                "release_group.comment",
                "release_group.name",
                "release_group.type.gid",
                "release_group.secondary_types.secondary_type.gid",
                "status.gid",
                "language.iso_code_3",
                "tags.count"]
)


SearchReleaseGroup = E(modelext.CustomReleaseGroup, [
    F("mbid", "gid"),
    F("releasegroup", "name"),
    F("alias", "aliases.name"),
    F("arid", "artist_credit.artists.artist.gid"),
    F("artist", "artist_credit.name"),
    F("artistname", "artist_credit.artists.artist.name"),
    F("creditname", "artist_credit.artists.name"),
    F("release", "releases.name"),
    F("reid", "releases.gid"),
    F("releases", "release_count", transformfunc=tfs.integer_sum, trigger=False),
    F("status", "releases.status.name"),
    F("comment", "comment"),
    F("tag", "tags.tag.name"),
    F("primarytype", "type.name"),
    F("secondarytype", "secondary_types.secondary_type.name")
],
    1.5,
    convert.convert_release_group,
    extrapaths=["artist_credit.artists.join_phrase",
                "artist_credit.artists.artist.aliases.begin_date",
                "artist_credit.artists.artist.aliases.end_date",
                "artist_credit.artists.artist.aliases.locale",
                "artist_credit.artists.artist.aliases.name",
                "artist_credit.artists.artist.aliases.primary_for_locale",
                "artist_credit.artists.artist.aliases.sort_name",
                "artist_credit.artists.artist.aliases.type.id",
                "artist_credit.artists.artist.aliases.type.name",
                "artist_credit.artists.artist.gid",
                "artist_credit.artists.artist.sort_name",
                "artist_credit.artists.artist.comment",
                "tags.count", "type.gid",
                "releases.status.gid",
                "secondary_types.secondary_type.gid"
                ]
)


SearchSeries = E(modelext.CustomSeries, [
    F("mbid", "gid"),
    F("alias", "aliases.name"),
    F("comment", "comment"),
    F("orderingattribute", "link_attribute_type.name"),
    F("series", "name"),
    F("tag", "tags.tag.name"),
    F("type", "type.name")
],
    1.5,
    convert.convert_series,
    extrapaths=["tags.count",
                "aliases.type.name", "aliases.type.id",
                "aliases.type.gid", "aliases.sort_name",
                "aliases.locale", "aliases.primary_for_locale",
                "aliases.begin_date", "aliases.end_date", "type.gid"]
)


SearchTag = E(models.Tag, [
    F("id", "id"),
    F("tag", "name")
],
    1.5,
    convert.convert_standalone_tag
)


SearchUrl = E(modelext.CustomURL, [
    F("mbid", "gid"),
    F("url", "url"),
    F("relationtype", ["artist_links.link.link_type.name",
                       "release_links.link.link_type.name"]),
    F("targetid", ["artist_links.artist.gid",
                   "release_links.release.gid"]),
    F("targettype", ["artist_links.__tablename__",
                     "release_links.__tablename__"],
      transformfunc=tfs.url_type),
],
    1.5,
    convert.convert_url,
    extrapaths=["artist_links.artist.gid",
                "artist_links.artist.name",
                "artist_links.artist.comment",
                "artist_links.artist.sort_name",
                "artist_links.link.link_type.name",
                "artist_links.link.link_type.gid",
                "artist_links.link.attributes.attribute_type.name",
                "artist_links.link.attributes.attribute_type.gid",
                "release_links.release.gid",
                "release_links.release.name",
                "release_links.release.comment",
                "release_links.link.link_type.name",
                "release_links.link.link_type.gid",
                "release_links.link.attributes.attribute_type.name",
                "release_links.link.attributes.attribute_type.gid",
                ]
)


SearchWork = E(modelext.CustomWork, [
    F("mbid", "gid"),
    F("work", "name"),
    F("alias", "aliases.name"),
    F("arid", "artist_links.artist.gid"),
    F("artist", "artist_links.artist.name"),
    F("comment", "comment"),
    F("iswc", "iswcs.iswc"),
    F("lang", "languages.language.iso_code_3"),
    F("recording", "recording_links.recording.name"),
    F("recording_count", "recording_count", transformfunc=tfs.integer_sum, trigger=False),
    F("rid", "recording_links.recording.gid"),
    F("tag", "tags.tag.name"),
    F("type", "type.name")
],
    1.5,
    convert.convert_work,
    extrapaths=["aliases.type.name", "aliases.type.id",
                "aliases.type.gid",
                "aliases.sort_name", "aliases.locale",
                "aliases.primary_for_locale",
                "aliases.begin_date", "aliases.end_date",
                "artist_links.link.link_type.name",
                "artist_links.link.link_type.gid",
                "artist_links.link.attributes.attribute_type.name",
                "artist_links.link.attributes.attribute_type.gid",
                "recording_links.link.link_type.name",
                "recording_links.link.link_type.gid",
                "recording_links.link.attributes.attribute_type.name",
                "recording_links.link.attributes.attribute_type.gid",
                "recording_links.recording.video",
                "tags.count", "type.gid"]
)


#: Maps core names to :class:`~sir.schema.searchentities.SearchEntity` objects.
SCHEMA = OrderedDict(sorted({
    # The dict gets sorted to guarantee a sorted order in `reindex`s --help
    "annotation": SearchAnnotation,
    "artist": SearchArtist,
    "area": SearchArea,
    "cdstub": SearchCDStub,
    "editor": SearchEditor,
    "event": SearchEvent,
    "instrument": SearchInstrument,
    "label": SearchLabel,
    "place": SearchPlace,
    "recording": SearchRecording,
    "release": SearchRelease,
    "release-group": SearchReleaseGroup,
    "series": SearchSeries,
    "tag": SearchTag,
    "url": SearchUrl,
    "work": SearchWork,
}.items(), key=lambda val: val[0]))


def generate_update_map():
    """
    Generates mapping from tables to Solr cores (entities) that depend on
    these tables and the columns of those tables. In addition provides a
    path along which data of an entity can be retrieved by performing a set
    of JOINs and a map of table names to SQLAlchemy ORM models and other useful
    mappings.

    Uses paths to determine the dependency.

    :rtype (dict, dict, dict, dict)
    """
    from sir.trigger_generation.paths import (unique_split_paths, last_model_in_path,
                                             second_last_model_in_path)

    paths = defaultdict(set)
    column_map = defaultdict(set)

    # Used to map table names to mbdata.models for indexing.
    models = {}
    # Used to map table names to core names while handling entity deletion.
    core_map = {}

    for core_name, entity in SCHEMA.items():
        # Entity itself:
        # TODO(roman): See if the line below is necessary, if there is a better way to implement this.
        mapped_table = class_mapper(entity.model).mapped_table.name
        core_map[mapped_table] = core_name
        paths[mapped_table].add((core_name, None))
        models[mapped_table] = entity.model
        # Related tables:
        for path in unique_split_paths([path for field in entity.fields
                                        for path in field.paths if field.trigger] + [path for path in entity.extrapaths or []]):
            model = last_model_in_path(entity.model, path)
            if model is not None:
                name = class_mapper(model).mapped_table.name
                paths[name].add((core_name, path))
                if name not in models:
                    models[name] = model

            # For generating column map
            model, _ = second_last_model_in_path(entity.model, path)
            prop_name = path.split(".")[-1]
            try:
                prop = getattr(model, prop_name).prop
                # We only care about columns, not relations
                if isinstance(prop, (ColumnProperty, CompositeProperty)):
                    # In case of Composite properties, there might be more
                    # than 1 columns involved
                    column_names = [col.name for col in prop.columns]
                    column_map[model.__table__.name].update(column_names)
                elif isinstance(prop, RelationshipProperty):
                    if prop.direction.name == 'MANYTOONE':
                        # We are assuming MB-DB uses only non-composite FKs.
                        # In case this changes in the future, `test.DBTest.test_non_composite_fk`
                        # will fail.
                        column_map[model.__table__.name].add(list(prop.local_columns)[0].name)
            # This happens in case of annotation and url paths
            # which have path to figure out the table name via transform funcs
            except AttributeError:
                pass
    return dict(paths), dict(column_map), models, core_map
