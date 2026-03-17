#!/usr/bin/env python
# -*- mode:Python; coding: utf-8 -*-

# ----------------------------------
# Created on the Mon Feb 23 2026 by Victor
#
# Copyright (c) 2026 - AmazingQuantum@UChile
# ----------------------------------
#
"""
Content of dummy.py

This document contains dummy functions, It also contains a model to follow to code.
"""


def wave_energy(frequency: float) -> float:
    """
    Compute photon energy from frequency.

    Parameters
    ----------
    frequency : float
        Frequency in Hz.

    Returns
    -------
    float
        Energy in Joules.
    """
    h = 6.626e-34  # Planck constant
    return h * frequency
