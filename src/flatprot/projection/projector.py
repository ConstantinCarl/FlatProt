# Copyright 2024 Tobias Olenyi.
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import numpy as np
from pathlib import Path
from typing import Dict, Optional

from ..structure.components import Structure


class ProjectionScope(Enum):
    STRUCTURE = "structure"  # Project entire structure together
    CHAIN = "chain"  # Project each chain independently


class Projector(ABC):
    """Base class for all projectors using template method pattern."""

    def __init__(self, scope: ProjectionScope = ProjectionScope.STRUCTURE):
        self.scope = scope
        self._cached_projections: Dict[str, np.ndarray] = {}
        self._structure_projection: Optional[np.ndarray] = None

    def project(self, structure: Structure) -> Dict[str, np.ndarray]:
        """Template method defining the projection workflow.

        Returns:
            Dictionary mapping chain IDs to their 2D coordinates
        """
        if self.scope == ProjectionScope.STRUCTURE:
            return self._project_whole_structure(structure)
        else:
            return self._project_individual_chains(structure)

    def _project_whole_structure(self, structure: Structure) -> Dict[str, np.ndarray]:
        """Projects entire structure using single transformation."""
        if self._structure_projection is None:
            # Get all coordinates
            all_coords = np.vstack(
                [self._get_chain_coordinates(chain) for chain in structure.values()]
            )
            self._structure_projection = self._calculate_projection(
                structure, all_coords
            )

        # Apply same transformation to each chain
        return {
            chain_id: self._apply_cached_projection(chain, self._structure_projection)
            for chain_id, chain in structure.items()
        }

    def _project_individual_chains(self, structure: Structure) -> Dict[str, np.ndarray]:
        """Projects each chain independently."""
        projections = {}
        for chain_id, chain in structure.items():
            if chain_id not in self._cached_projections:
                coords = self._get_chain_coordinates(chain)
                self._cached_projections[chain_id] = self._calculate_projection(
                    structure, coords, chain_id
                )

            projections[chain_id] = self._apply_cached_projection(
                chain, self._cached_projections[chain_id]
            )
        return projections

    @abstractmethod
    def _calculate_projection(
        self,
        structure: Structure,
        coordinates: np.ndarray,
        chain_id: Optional[str] = None,
    ) -> np.ndarray:
        """Calculate projection for given coordinates.

        Args:
            structure: Complete structure (for context)
            coordinates: Coordinates to project
            chain_id: Chain ID if projecting single chain, None for whole structure

        Returns:
            Projected 2D coordinates
        """
        pass

    @abstractmethod
    def _get_chain_coordinates(self, chain) -> np.ndarray:
        """Extract coordinates from chain."""
        pass

    @abstractmethod
    def _apply_cached_projection(
        self, chain, cached_projection: np.ndarray
    ) -> np.ndarray:
        """Apply cached projection to chain coordinates."""
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """Saves projection parameters.

        Args:
            path: Where to save the projection
        """
        pass

    @abstractmethod
    def load(self, path: Path) -> None:
        """Loads projection parameters.

        Args:
            path: From where to load the projection
        """
        pass
