import datetime

from _pytest.skipping import Skip
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestHotel


@freeze_time("1980-01-01")
class TestPmsRoomTypeRestriction(TestHotel):
    def create_common_scenario(self):
        # product.pricelist
        self.test_pricelist1 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
            }
        )
        # pms.room.type.restriction
        self.test_room_type_restriction1 = self.env["pms.room.type.restriction"].create(
            {
                "name": "Restriction plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.test_pricelist1.id])],
            }
        )
        # pms.property
        self.test_property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist1.id,
                "default_restriction_id": self.test_room_type_restriction1.id,
            }
        )
        # pms.room.type.class
        self.test_room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room"}
        )

        # pms.room.type
        self.test_room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Single Test",
                "code_type": "SNG_Test",
                "class_id": self.test_room_type_class.id,
            }
        )
        # pms.room.type
        self.test_room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Double Test",
                "code_type": "DBL_Test",
                "class_id": self.test_room_type_class.id,
            }
        )
        # pms.room
        self.test_room1_double = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 201 test",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        # pms.room
        self.test_room2_double = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Double 202 test",
                "room_type_id": self.test_room_type_double.id,
                "capacity": 2,
            }
        )
        # pms.room
        # self.test_room3_double = self.env["pms.room"].create(
        #     {
        #         "pms_property_id": self.test_property.id,
        #         "name": "Double 203 test",
        #         "room_type_id": self.test_room_type_double.id,
        #         "capacity": 2,
        #     }
        # )
        # # pms.room
        # self.test_room4_double = self.env["pms.room"].create(
        #     {
        #         "pms_property_id": self.test_property.id,
        #         "name": "Double 204 test",
        #         "room_type_id": self.test_room_type_double.id,
        #         "capacity": 2,
        #     }
        # )
        # pms.room
        self.test_room1_single = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Single 101 test",
                "room_type_id": self.test_room_type_single.id,
                "capacity": 1,
            }
        )
        # pms.room
        self.test_room2_single = self.env["pms.room"].create(
            {
                "pms_property_id": self.test_property.id,
                "name": "Single 102 test",
                "room_type_id": self.test_room_type_single.id,
                "capacity": 1,
            }
        )

    @Skip
    def test_availability_rooms_all(self):
        # TEST CASE
        # get availability withouth restrictions

        # ARRANGE
        self.create_common_scenario()

        checkin = fields.date.today()
        checkout = (fields.datetime.today() + datetime.timedelta(days=4)).date()
        test_rooms_double_rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", self.test_property.id)]
        )

        # ACT
        result = self.env["pms.room.type.restriction"].rooms_available(
            checkin=checkin,
            checkout=checkout,
        )
        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no  restriction for them.",
        )

    @Skip
    def test_availability_rooms_all_lines(self):
        # TEST CASE
        # get availability withouth restrictions
        # given reservation lines to not consider

        # ARRANGE
        self.create_common_scenario()
        checkin = fields.date.today()
        checkout = (fields.datetime.today() + datetime.timedelta(days=4)).date()
        test_rooms_double_rooms = self.env["pms.room"].search(
            [("pms_property_id", "=", self.test_property.id)]
        )
        test_reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": checkin,
                "checkout": checkout,
            }
        )

        # ACT
        result = self.env["pms.room.type.restriction"].rooms_available(
            checkin=checkin,
            checkout=checkout,
            current_lines=test_reservation.reservation_line_ids.ids,
        )
        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no  restriction for them.",
        )

    @Skip
    def test_availability_rooms_room_type(self):
        # TEST CASE
        # get availability withouth restrictions
        # given a room type

        # ARRANGE
        self.create_common_scenario()
        test_rooms_double_rooms = self.env["pms.room"].search(
            [
                ("pms_property_id", "=", self.test_property.id),
                ("room_type_id", "=", self.test_room_type_double.id),
            ]
        )

        # ACT
        result = self.env["pms.room.type.restriction"].rooms_available(
            checkin=fields.date.today(),
            checkout=(fields.datetime.today() + datetime.timedelta(days=4)).date(),
            room_type_id=self.test_room_type_double.id,
        )

        # ASSERT
        obtained = all(elem.id in result.ids for elem in test_rooms_double_rooms)
        self.assertTrue(
            obtained,
            "Availability should contain the test rooms"
            "because there's no  restriction for them.",
        )

    @Skip
    def test_availability_closed_no_room_type(self):
        # TEST CASE:
        # coverage for 2 points:
        # 1. without room type, restrictions associated with the pricelist are applied
        # 2. restriction rule "closed" is taken into account

        # ARRANGE
        self.create_common_scenario()
        self.test_room_type_restriction1_item1 = self.env[
            "pms.room.type.restriction.item"
        ].create(
            {
                "restriction_id": self.test_room_type_restriction1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,  # <- (1/2)
            }
        )
        # ACT
        result = self.env["pms.room.type.restriction"].rooms_available(
            checkin=fields.date.today(),
            checkout=(fields.datetime.today() + datetime.timedelta(days=4)).date(),
            # room_type_id=False, # <-  (2/2)
            pricelist=self.test_pricelist1.id,
        )
        # ASSERT
        self.assertNotIn(
            self.test_room_type_double,
            result.mapped("room_type_id"),
            "Availability should not contain rooms of a type "
            "which its restriction rules applies",
        )

    @Skip
    def test_availability_restrictions(self):
        # TEST CASE
        # the availability should take into acount restriction rules:
        # closed_arrival, closed_departure, min_stay, max_stay,
        # min_stay_arrival, max_stay_arrival

        # ARRANGE
        self.create_common_scenario()

        self.test_room_type_restriction1_item1 = self.env[
            "pms.room.type.restriction.item"
        ].create(
            {
                "restriction_id": self.test_room_type_restriction1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=0)).date(),
            }
        )

        checkin = fields.date.today()
        checkout = (fields.datetime.today() + datetime.timedelta(days=4)).date()

        test_cases = [
            {
                "closed": False,
                "closed_arrival": True,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "quota": -1,
                "max_avail": -1,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": True,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "quota": -1,
                "max_avail": -1,
                "date": checkout,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 5,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "quota": -1,
                "max_avail": -1,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 2,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "quota": -1,
                "max_avail": -1,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 5,
                "max_stay_arrival": 0,
                "quota": -1,
                "max_avail": -1,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 3,
                "quota": -1,
                "max_avail": -1,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "quota": 0,
                "max_avail": -1,
                "date": checkin,
            },
            {
                "closed": False,
                "closed_arrival": False,
                "closed_departure": False,
                "min_stay": 0,
                "max_stay": 0,
                "min_stay_arrival": 0,
                "max_stay_arrival": 0,
                "quota": -1,
                "max_avail": 0,
                "date": checkin,
            },
        ]

        for test_case in test_cases:
            with self.subTest(k=test_case):

                # ACT
                self.test_room_type_restriction1_item1.write(test_case)

                result = self.env["pms.room.type.restriction"].rooms_available(
                    checkin=checkin,
                    checkout=checkout,
                    room_type_id=self.test_room_type_double.id,
                    pricelist=self.test_pricelist1.id,
                )

                # ASSERT
                self.assertNotIn(
                    self.test_room_type_double,
                    result.mapped("room_type_id"),
                    "Availability should not contain rooms of a type "
                    "which its restriction rules applies",
                )

    @Skip
    @freeze_time("1980-11-01")
    def test_restriction_on_create_reservation(self):
        # TEST CASE
        # a restriction should be applied that would prevent the
        # creation of reservations

        # ARRANGE
        self.create_common_scenario()
        self.test_room_type_restriction1_item1 = self.env[
            "pms.room.type.restriction.item"
        ].create(
            {
                "restriction_id": self.test_room_type_restriction1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
            }
        )

        checkin = datetime.datetime.now()
        checkout = datetime.datetime.now() + datetime.timedelta(days=4)

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Restriction should be applied that would"
            " prevent the creation of the reservation.",
        ):
            self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.test_property.id,
                    "checkin": checkin,
                    "checkout": checkout,
                    "adults": 2,
                    "room_type_id": self.test_room_type_double.id,
                    "pricelist_id": self.test_pricelist1.id,
                }
            )

    @Skip
    @freeze_time("1980-11-01")
    def test_restriction_on_create_splitted_reservation(self):
        # TEST CASE
        # a restriction should be applied that would prevent the
        # creation of reservations including splitted reservations.

        # ARRANGE
        self.create_common_scenario()
        self.test_room_type_restriction1_item1 = self.env[
            "pms.room.type.restriction.item"
        ].create(
            {
                "restriction_id": self.test_room_type_restriction1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": (fields.datetime.today() + datetime.timedelta(days=2)).date(),
                "closed": True,
            }
        )

        checkin_test = datetime.datetime.now()
        checkout_test = datetime.datetime.now() + datetime.timedelta(days=4)

        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "preferred_room_id": self.test_room1_double.id,
            }
        )

        self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=2),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=4),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "preferred_room_id": self.test_room2_double.id,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Restriction should be applied that would"
            " prevent the creation of splitted reservation.",
        ):
            self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.test_property.id,
                    "checkin": checkin_test,
                    "checkout": checkout_test,
                    "adults": 2,
                    "room_type_id": self.test_room_type_double.id,
                    "pricelist_id": self.test_pricelist1.id,
                }
            )

    @Skip
    @freeze_time("1980-11-01")
    def test_restriction_update_quota_on_create_reservation(self):
        # TEST CASE
        # quota rule is changed after creating a reservation
        # with pricelist linked to a restriction_item that applies

        # ARRANGE
        self.create_common_scenario()

        self.test_room_type_restriction1_item1 = self.env[
            "pms.room.type.restriction.item"
        ].create(
            {
                "restriction_id": self.test_room_type_restriction1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": datetime.date.today(),
                "quota": 1,
            }
        )
        r1 = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "pricelist_id": self.test_pricelist1.id,
            }
        )
        r1.flush()
        with self.assertRaises(
            ValidationError,
            msg="The quota shouldnt be enough to create a new reservation",
        ):
            self.env["pms.reservation"].create(
                {
                    "pms_property_id": self.test_property.id,
                    "checkin": datetime.date.today(),
                    "checkout": datetime.date.today() + datetime.timedelta(days=1),
                    "adults": 2,
                    "room_type_id": self.test_room_type_double.id,
                    "pricelist_id": self.test_pricelist1.id,
                }
            )

    @freeze_time("1980-11-01")
    def test_restriction_update_quota_on_update_reservation(self):
        # TEST CASE
        # quota rule is restored after creating a reservation
        # with pricelist linked to a restriction_item that applies
        # and then modify the pricelist of the reservation and
        # no restriction applies

        # ARRANGE
        self.create_common_scenario()
        test_quota = 2
        test_pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 2",
            }
        )
        restriction = self.env["pms.room.type.restriction.item"].create(
            {
                "restriction_id": self.test_room_type_restriction1.id,
                "room_type_id": self.test_room_type_double.id,
                "date": datetime.date.today(),
                "quota": test_quota,
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "pms_property_id": self.test_property.id,
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "adults": 2,
                "room_type_id": self.test_room_type_double.id,
                "pricelist_id": self.test_pricelist1.id,
            }
        )

        # ACT
        reservation.pricelist_id = test_pricelist2.id
        reservation.flush()
        self.assertEqual(
            test_quota,
            restriction.quota,
            "The quota should be restored after changing the reservation's pricelist",
        )
