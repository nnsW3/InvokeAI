import { IconButton } from '@invoke-ai/ui-library';
import { useAppDispatch } from 'app/store/storeHooks';
import { useBoolean } from 'common/hooks/useBoolean';
import { useEntityIdentifierContext } from 'features/controlLayers/contexts/EntityIdentifierContext';
import { useEntityIsEnabled } from 'features/controlLayers/hooks/useEntityIsEnabled';
import { entityIsEnabledToggled } from 'features/controlLayers/store/canvasSlice';
import { memo, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { PiCheckBold } from 'react-icons/pi';

export const CanvasEntityEnabledToggle = memo(() => {
  const { t } = useTranslation();
  const entityIdentifier = useEntityIdentifierContext();
  const ref = useRef<HTMLButtonElement>(null);
  const isEnabled = useEntityIsEnabled(entityIdentifier);
  const dispatch = useAppDispatch();
  const onClick = useCallback(() => {
    dispatch(entityIsEnabledToggled({ entityIdentifier }));
  }, [dispatch, entityIdentifier]);
  const isHovered = useBoolean(false);

  return (
    <IconButton
      ref={ref}
      size="sm"
      onMouseOver={isHovered.setTrue}
      onMouseOut={isHovered.setFalse}
      aria-label={t(isEnabled ? 'common.enabled' : 'common.disabled')}
      tooltip={t(isEnabled ? 'common.enabled' : 'common.disabled')}
      variant="ghost"
      icon={isEnabled || isHovered.isTrue ? <PiCheckBold /> : undefined}
      onClick={onClick}
    />
  );
});

CanvasEntityEnabledToggle.displayName = 'CanvasEntityEnabledToggle';
