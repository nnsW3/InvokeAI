import { Flex, Spacer } from '@invoke-ai/ui-library';
import { EntityListActionBarAddLayerButton } from 'features/controlLayers/components/CanvasEntityList/EntityListActionBarAddLayerMenuButton';
import { EntityListActionBarDeleteButton } from 'features/controlLayers/components/CanvasEntityList/EntityListActionBarDeleteButton';
import { SelectedEntityOpacity } from 'features/controlLayers/components/CanvasEntityList/EntityListActionBarSelectedEntityOpacity';
import { memo } from 'react';

export const EntityListActionBar = memo(() => {
  return (
    <Flex w="full" py={1} px={1} gap={2}>
      <SelectedEntityOpacity />
      <Spacer />
      <EntityListActionBarAddLayerButton />
      <EntityListActionBarDeleteButton />
    </Flex>
  );
});

EntityListActionBar.displayName = 'EntityListActionBar';
